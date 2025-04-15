import random
from datetime import timedelta
from typing import List, Optional, Union

import requests
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.access_tokens import schemas as access_token_schemas
from app.api.access_tokens.crud import access_token as access_token_crud
from app.api.base_crud import CRUDBase
from app.api.citizens import models, schemas
from app.api.citizens.schemas import CitizenPoaps, CitizenPoapsByPopup, PoapClaim
from app.api.email_logs.crud import email_log
from app.api.email_logs.schemas import EmailEvent
from app.core.config import settings
from app.core.locks import DistributedLock
from app.core.logger import logger
from app.core.security import SYSTEM_TOKEN, TokenData
from app.core.utils import create_spice, current_time

POAP_TOKEN_ID = 'poap'
POAP_REFRESH_LOCK = DistributedLock('poap_token_refresh')


def _refresh_poap_token():
    url = 'https://auth.accounts.poap.xyz/oauth/token'
    headers = {'Content-Type': 'application/json'}
    data = {
        'audience': 'https://api.poap.tech',
        'grant_type': 'client_credentials',
        'client_id': settings.POAP_CLIENT_ID,
        'client_secret': settings.POAP_CLIENT_SECRET,
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    access_token = response.json()['access_token']
    expires_in = response.json()['expires_in']
    logger.info('POAP token refreshed. Expires in: %s', expires_in)
    expires_at = current_time() + timedelta(seconds=expires_in)
    return access_token, expires_at


def _get_poap_token(db: Session):
    poap_token = access_token_crud.get_by_name(db, POAP_TOKEN_ID)
    if not poap_token:
        # If token doesn't exist, acquire lock and create it
        with POAP_REFRESH_LOCK.acquire(db):
            # Check again after acquiring lock in case another process created it
            poap_token = access_token_crud.get_by_name(db, POAP_TOKEN_ID)
            if poap_token:
                return poap_token.value
            logger.info('POAP token not found, creating new one')
            token, expires_at = _refresh_poap_token()
            update_obj = access_token_schemas.AccessTokenCreate(
                name=POAP_TOKEN_ID, value=token, expires_at=expires_at
            )
            poap_token = access_token_crud.create(db, update_obj)
            logger.info('POAP token created. Expires at: %s', poap_token.expires_at)
    elif poap_token.expires_at < current_time() + timedelta(minutes=10):
        # If token is about to expire, acquire lock and refresh it
        with POAP_REFRESH_LOCK.acquire(db):
            # Check expiration again after acquiring lock in case another process refreshed it
            poap_token = access_token_crud.get_by_name(db, POAP_TOKEN_ID)
            if poap_token.expires_at >= current_time() + timedelta(minutes=10):
                return poap_token.value
            logger.info('Refreshing POAP token. Expires at: %s', poap_token.expires_at)
            token, expires_at = _refresh_poap_token()
            update_obj = access_token_schemas.AccessTokenUpdate(
                value=token, expires_at=expires_at
            )
            poap_token = access_token_crud.update_by_name(db, POAP_TOKEN_ID, update_obj)
            logger.info('POAP token updated. Expires at: %s', poap_token.expires_at)
    return poap_token.value


def _get_poap_qr(qr_hash: str, db: Session):
    poap_token = _get_poap_token(db)
    url = f'https://api.poap.tech/actions/claim-qr?qr_hash={qr_hash}'
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {poap_token}',
        'X-API-Key': settings.POAP_API_KEY,
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(
            f'Failed to get POAP QR: {response.status_code} {response.text}'
        )

    return {
        'claimed': response.json()['claimed'],
        'is_active': response.json()['is_active'],
        'name': response.json()['event']['name'],
        'description': response.json()['event']['description'],
        'image_url': response.json()['event']['image_url'],
    }


class CRUDCitizen(
    CRUDBase[models.Citizen, schemas.CitizenCreate, schemas.CitizenCreate]
):
    def _check_permission(self, db_obj: models.Citizen, user: TokenData) -> bool:
        return user == SYSTEM_TOKEN or db_obj.id == user.citizen_id

    def find(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[schemas.CitizenFilter] = None,
        user: Optional[TokenData] = None,
    ) -> List[models.Citizen]:
        if user:
            filters = filters or schemas.CitizenFilter()
            filters.id = user.citizen_id
        return super().find(db, skip, limit, filters)

    def get_by_email(self, db: Session, email: str) -> Optional[models.Citizen]:
        return db.query(self.model).filter(self.model.primary_email == email).first()

    def get_or_create(
        self, db: Session, citizen: schemas.CitizenCreate
    ) -> models.Citizen:
        existing_citizen = self.get_by_email(db, citizen.primary_email)
        if existing_citizen:
            return existing_citizen
        logger.info('Citizen not found, creating: %s', citizen)
        return self.create(db, citizen)

    def create(
        self,
        db: Session,
        obj: Union[schemas.CitizenCreate, schemas.InternalCitizenCreate],
        user: Optional[TokenData] = None,
    ) -> models.Citizen:
        to_create = schemas.InternalCitizenCreate(**obj.model_dump())
        to_create.spice = create_spice()
        citizen = super().create(db, to_create)
        return citizen

    def signup(self, db: Session, *, obj: schemas.CitizenCreate) -> models.Citizen:
        citizen = self.create(db, obj)
        email_log.send_login_mail(citizen.primary_email, citizen.spice, citizen.id)
        return citizen

    def authenticate(
        self,
        db: Session,
        *,
        email: str,
        popup_slug: Optional[str] = None,
        use_code: bool = False,
    ) -> models.Citizen:
        citizen = self.get_by_email(db, email)

        code = random.randint(100000, 999999) if use_code else None
        code_expiration = current_time() + timedelta(minutes=5) if use_code else None

        if not citizen:
            to_create = schemas.InternalCitizenCreate(
                primary_email=email,
                code=code,
                code_expiration=code_expiration,
            )
            citizen = self.create(db, to_create)
        else:
            citizen.spice = create_spice()
            if code:
                citizen.code = code
                citizen.code_expiration = code_expiration
            db.commit()
            db.refresh(citizen)

        if code:
            email_log.send_mail(
                email,
                event=EmailEvent.AUTH_CITIZEN_BY_CODE.value,
                popup_slug=popup_slug,
                params={'code': code, 'email': email},
                spice=citizen.spice,
                entity_type='citizen',
                entity_id=citizen.id,
                citizen_id=citizen.id,
            )
        else:
            email_log.send_login_mail(email, citizen.spice, citizen.id, popup_slug)

        return {'message': 'Mail sent successfully'}

    def login(
        self,
        db: Session,
        *,
        email: str,
        spice: Optional[str] = None,
        code: Optional[int] = None,
    ) -> models.Citizen:
        if not spice and not code:
            raise HTTPException(
                status_code=400, detail='Either spice or code must be provided'
            )

        citizen = self.get_by_email(db, email)
        if not citizen:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Citizen not found',
            )
        if spice and citizen.spice != spice:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid spice',
            )
        if code:
            if citizen.code != code:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Invalid code',
                )
            if citizen.code_expiration < current_time():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Code expired',
                )

        citizen.email_validated = True
        db.commit()
        db.refresh(citizen)
        return citizen

    def get_poaps_from_citizen(self, db: Session, user: TokenData) -> CitizenPoaps:
        citizen: models.Citizen = self.get(db, user.citizen_id, user)
        response = CitizenPoaps(results=[])
        for application in citizen.applications:
            poaps = []
            for attendee in application.attendees:
                if attendee.poap_url:
                    qr_hash = attendee.poap_url.split('/')[-1]
                    poap_data = _get_poap_qr(qr_hash, db)
                    poaps.append(
                        PoapClaim(
                            attendee_id=attendee.id,
                            attendee_name=attendee.name,
                            attendee_email=attendee.email,
                            attendee_category=attendee.category,
                            poap_url=attendee.poap_url,
                            poap_name=poap_data['name'],
                            poap_description=poap_data['description'],
                            poap_image_url=poap_data['image_url'],
                            poap_claimed=poap_data['claimed'],
                            poap_is_active=poap_data['is_active'],
                        )
                    )
            if poaps:
                response.results.append(
                    CitizenPoapsByPopup(
                        popup_id=application.popup_city_id,
                        popup_name=application.popup_city.name,
                        poaps=poaps,
                    )
                )

        return response


citizen = CRUDCitizen(models.Citizen)
