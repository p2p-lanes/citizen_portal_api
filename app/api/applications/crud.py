from typing import List, Optional, Tuple, Union

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.applications import models, schemas
from app.api.attendees import schemas as attendees_schemas
from app.api.attendees.crud import attendee as attendees_crud
from app.api.base_crud import CRUDBase
from app.api.citizens.models import Citizen as CitizenModel
from app.api.email_logs.crud import email_log
from app.api.email_logs.schemas import EmailEvent
from app.api.organizations.crud import organization as organization_crud
from app.api.popup_city.models import PopUpCity
from app.core.logger import logger
from app.core.security import TokenData
from app.core.utils import current_time


def _requested_a_discount(
    application: Union[models.Application, schemas.Application],
    requires_approval: bool,
) -> bool:
    """
    Determines if a discount has been requested based on the application state.
    Works with both database models (`models.Application`) and schemas (`schemas.Application`).
    """
    if requires_approval:
        return application.scholarship_request

    return application.is_renter or application.scholarship_request


def calculate_status(
    application: Union[models.Application, schemas.Application],
    requires_approval: bool,
    reviews_status: Optional[schemas.ApplicationStatus] = None,
) -> Tuple[schemas.ApplicationStatus, bool]:
    submitted_at = application.submitted_at
    requested_a_discount = _requested_a_discount(application, requires_approval)

    if reviews_status == schemas.ApplicationStatus.REJECTED:
        return schemas.ApplicationStatus.REJECTED, requested_a_discount

    discount_assigned = getattr(application, 'discount_assigned', None)
    missing_discount = requested_a_discount and discount_assigned is None
    if not requires_approval and not requested_a_discount:
        return schemas.ApplicationStatus.ACCEPTED, requested_a_discount

    if not reviews_status or missing_discount:
        return (
            schemas.ApplicationStatus.IN_REVIEW
            if submitted_at
            else schemas.ApplicationStatus.DRAFT
        ), requested_a_discount

    return reviews_status, requested_a_discount


def _send_application_received_mail(application: models.Application):
    email_log.send_mail(
        receiver_mail=application.email,
        event=EmailEvent.APPLICATION_RECEIVED.value,
        popup_city=application.popup_city,
        entity_type='application',
        entity_id=application.id,
    )


class CRUDApplication(
    CRUDBase[models.Application, schemas.ApplicationCreate, schemas.ApplicationCreate]
):
    def _update_citizen_profile(self, db: Session, application: models.Application):
        citizen = application.citizen

        citizen.first_name = application.first_name
        citizen.last_name = application.last_name
        citizen.telegram = application.telegram
        citizen.role = application.role
        citizen.residence = application.residence
        citizen.social_media = application.social_media
        citizen.age = application.age
        citizen.gender = application.gender
        citizen.eth_address = application.eth_address
        citizen.referral = application.referral

        if application.organization:
            org = organization_crud.get_or_create(db, application.organization)
            application.organization_id = org.id
            citizen.organization_id = org.id

        db.commit()
        db.refresh(citizen)

        return citizen

    def _check_permission(self, db_obj: models.Application, user: TokenData) -> bool:
        user_id = user.citizen_id
        is_leader = db_obj.group.is_leader(user_id) if db_obj.group else False
        return db_obj.citizen_id == user_id or is_leader

    def get_by_citizen_and_popup_city(
        self, db: Session, citizen_id: int, popup_city_id: int
    ) -> Optional[models.Application]:
        return (
            db.query(models.Application)
            .filter(
                models.Application.citizen_id == citizen_id,
                models.Application.popup_city_id == popup_city_id,
            )
            .first()
        )

    def create(
        self,
        db: Session,
        obj: schemas.ApplicationCreate,
        user: TokenData,
    ) -> models.Application:
        from app.api.groups.crud import group as groups_crud

        logger.info('Creating application: %s', obj)
        citizen_id = obj.citizen_id
        citizen = db.query(CitizenModel).filter(CitizenModel.id == citizen_id).first()
        if not citizen:
            raise HTTPException(status_code=404, detail='Citizen not found')

        group = None
        if obj.group_id:
            group = groups_crud.get(db, obj.group_id, user)
            if not group.is_leader(user.citizen_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='Not authorized to create application for another citizen',
                )
            obj.status = schemas.ApplicationStatus.ACCEPTED
        elif obj.citizen_id != user.citizen_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Not authorized to create application for another citizen',
            )

        logger.info('Citizen found: %s %s', citizen.id, citizen.primary_email)
        email = citizen.primary_email
        submitted_at = (
            current_time()
            if obj.status == schemas.ApplicationStatus.IN_REVIEW
            else None
        )
        obj = schemas.InternalApplicationCreate(
            **obj.model_dump(),
            email=email,
            submitted_at=submitted_at,
        )

        if obj.status != schemas.ApplicationStatus.DRAFT and not group:
            popup_city_id = obj.popup_city_id
            popup = db.query(PopUpCity).filter(PopUpCity.id == popup_city_id).first()
            requires_approval = popup.requires_approval if popup else False

            obj.status, obj.requested_discount = calculate_status(
                obj, requires_approval=requires_approval
            )

        application = super().create(db, obj)

        attendee = attendees_schemas.AttendeeCreate(
            name=f'{obj.first_name} {obj.last_name}'.strip(),
            category='main',
            email=email,
            group_id=group.id if group else None,
        )
        self.create_attendee(db, application.id, attendee, user)

        if application.status == schemas.ApplicationStatus.IN_REVIEW:
            _send_application_received_mail(application)

        self._update_citizen_profile(db, application)
        return application

    def update(
        self,
        db: Session,
        id: int,
        obj: schemas.ApplicationUpdate,
        user: TokenData,
    ) -> models.Application:
        application = super().update(db, id, obj, user)
        requires_approval = application.popup_city.requires_approval

        if obj.status == schemas.ApplicationStatus.IN_REVIEW:
            if application.submitted_at is None:
                application.submitted_at = current_time()

            application.clean_reviews()
            application.status, application.requested_discount = calculate_status(
                application, requires_approval=requires_approval
            )
            if application.status == schemas.ApplicationStatus.IN_REVIEW:
                _send_application_received_mail(application)
        else:
            requested_discount = _requested_a_discount(application, requires_approval)
            application.requested_discount = requested_discount

        self._update_citizen_profile(db, application)

        db.add(application)
        db.commit()
        db.refresh(application)
        return application

    def find(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[schemas.ApplicationFilter] = None,
        user: Optional[TokenData] = None,
    ) -> List[models.Application]:
        if user:
            filters = filters or schemas.ApplicationFilter()
            filters.citizen_id = user.citizen_id
        return super().find(db, skip, limit, filters, user)

    def create_attendee(
        self,
        db: Session,
        application_id: int,
        attendee: attendees_schemas.AttendeeCreate,
        user: TokenData,
    ) -> models.Application:
        application = self.get(db, application_id, user)
        existing_categories = {a.category for a in application.attendees}
        if (
            attendee.category in ['main', 'spouse']
            and attendee.category in existing_categories
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Attendee {attendee.category} already exists',
            )
        existing_emails = [a.email for a in application.attendees if a.email]
        if attendee.email and attendee.email in existing_emails:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Attendee {attendee.email} already exists',
            )
        attendee = attendees_schemas.InternalAttendeeCreate(
            **attendee.model_dump(), application_id=application_id
        )
        attendee = attendees_crud.create(db, attendee, user)
        return application

    def update_attendee(
        self,
        db: Session,
        application_id: int,
        attendee_id: int,
        attendee: attendees_schemas.AttendeeUpdate,
        user: TokenData,
    ) -> models.Application:
        application = self.get(db, application_id, user)
        existing_emails = [
            a.email for a in application.attendees if a.email and a.id != attendee_id
        ]
        if attendee.email and attendee.email in existing_emails:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Attendee {attendee.email} already exists',
            )
        _ = attendees_crud.update(db, attendee_id, attendee, user)
        return application

    def delete_attendee(
        self,
        db: Session,
        application_id: int,
        attendee_id: int,
        user: TokenData,
    ) -> models.Application:
        application = self.get(db, application_id, user)
        if attendee_id not in [a.id for a in application.attendees]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Attendee not found',
            )
        attendee = attendees_crud.get(db, attendee_id, user)
        if attendee.category == 'main':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Cannot delete main attendee',
            )
        attendees_crud.delete(db, attendee_id, user)
        return application

    def get_attendees_directory(self, db: Session, popup_city_id: int, user: TokenData):
        filters = schemas.ApplicationFilter(popup_city_id=popup_city_id)
        skip = 0
        limit = 100
        attendees = []
        for application in self.find(
            db,
            skip=skip,
            limit=limit,
            filters=filters,
        ):
            main_attendee = next(
                (a for a in application.attendees if a.category == 'main')
            )
            if not main_attendee.products:
                continue

            check_in, check_out = None, None
            for p in main_attendee.products:
                if not check_in or (p.start_date and p.start_date < check_in):
                    check_in = p.start_date
                if not check_out or (p.end_date and p.end_date > check_out):
                    check_out = p.end_date

            a = {
                'first_name': application.first_name,
                'last_name': application.last_name,
                'email': application.email,
                'telegram': application.telegram,
                'brings_kids': application.brings_kids,
                'role': application.role,
                'organization': application.organization,
                'participation': main_attendee.products,
                'check_in': check_in,
                'check_out': check_out,
            }

            if application.info_not_shared:
                for f in application.info_not_shared:
                    a[f] = schemas.HIDDEN_VALUE

            attendees.append(a)
            skip += limit

        return attendees


application = CRUDApplication(models.Application)
