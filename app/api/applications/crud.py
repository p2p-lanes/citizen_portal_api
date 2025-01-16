from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.applications import models, schemas
from app.api.applications.attendees import schemas as attendees_schemas
from app.api.applications.attendees.crud import attendee as attendees_crud
from app.api.base_crud import CRUDBase
from app.api.citizens.models import Citizen as CitizenModel
from app.api.popup_city.crud import popup_city
from app.api.popup_city.models import PopUpCity
from app.core.mail import send_application_received_mail
from app.core.security import TokenData


class CRUDApplication(
    CRUDBase[models.Application, schemas.ApplicationCreate, schemas.ApplicationCreate]
):
    def _check_permission(self, db_obj: models.Application, user: TokenData) -> bool:
        return db_obj.citizen_id == user.citizen_id

    def create(
        self,
        db: Session,
        obj: schemas.ApplicationCreate,
        user: TokenData,
    ) -> models.Application:
        if obj.citizen_id != user.citizen_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Not authorized to create application for another citizen',
            )
        citizen = (
            db.query(CitizenModel).filter(CitizenModel.id == obj.citizen_id).first()
        )
        if not citizen:
            raise HTTPException(status_code=404, detail='Citizen not found')
        email = citizen.primary_email
        submitted_at = (
            datetime.utcnow()
            if obj.status == schemas.ApplicationStatus.IN_REVIEW
            else None
        )
        obj = schemas.InternalApplicationCreate(
            **obj.model_dump(),
            email=email,
            submitted_at=submitted_at,
        )

        if obj.status and obj.status != schemas.ApplicationStatus.DRAFT:
            popup_city_id = obj.popup_city_id
            requires_approval = (
                db.query(PopUpCity).filter(PopUpCity.id == popup_city_id).first()
            ).requires_approval
            if requires_approval:
                _template = popup_city.get_email_template(
                    db, popup_city_id, 'application-received'
                )
                send_application_received_mail(receiver_mail=email, template=_template)
            elif obj.status == schemas.ApplicationStatus.IN_REVIEW:
                obj.status = schemas.ApplicationStatus.ACCEPTED

        application = super().create(db, obj)
        attendee = attendees_schemas.AttendeeCreate(
            name=f'{obj.first_name} {obj.last_name}'.strip(),
            category='main',
            email=email,
        )
        self.create_attendee(db, application.id, attendee, user)
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

        if obj.status != schemas.ApplicationStatus.DRAFT:
            if (
                application.submitted_at is None
                and obj.status == schemas.ApplicationStatus.IN_REVIEW
            ):
                application.submitted_at = datetime.utcnow()

            if requires_approval:
                application.clean_reviews()
                popup_city_id = application.popup_city_id
                _template = popup_city.get_email_template(
                    db, popup_city_id, 'application-received'
                )
                send_application_received_mail(
                    receiver_mail=application.email, template=_template
                )
            elif (
                obj.status == schemas.ApplicationStatus.IN_REVIEW
                and not obj.is_renter
                and not obj.builder_boolean
                and not obj.scholarship_request
            ):
                application.status = schemas.ApplicationStatus.ACCEPTED
            db.commit()

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
