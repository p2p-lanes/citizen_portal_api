from typing import List, Optional, Union

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.applications.crud import application as applications_crud
from app.api.applications.schemas import (
    Application,
    ApplicationCreate,
    ApplicationWithAuth,
)
from app.api.base_crud import CRUDBase
from app.api.citizens.crud import citizen as citizens_crud
from app.api.citizens.schemas import CitizenCreate
from app.api.groups import models, schemas
from app.core.security import SYSTEM_TOKEN, TokenData


class CRUDGroup(CRUDBase[models.Group, schemas.GroupBase, schemas.GroupBase]):
    def _check_permission(self, db_obj: models.Group, user: TokenData) -> bool:
        """Verifies if user has permission to access this group. Returns True if allowed."""
        if not user:
            return False
        if user == SYSTEM_TOKEN:
            return True

        return any(leader.id == user.citizen_id for leader in db_obj.leaders)

    def find(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[schemas.GroupFilter] = None,
        user: Optional[TokenData] = None,
        sort_by: str = 'created_at',
        sort_order: str = 'desc',
    ) -> List[models.Group]:
        """Only return groups where the user is a leader"""
        if not user:
            return []

        query = db.query(self.model)
        query = query.join(
            models.GroupLeader, models.GroupLeader.group_id == self.model.id
        ).filter(models.GroupLeader.citizen_id == user.citizen_id)

        query = self._apply_filters(query, filters)

        if not hasattr(self.model, sort_by):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Invalid sort field: {sort_by}',
            )

        order_by = getattr(self.model, sort_by)
        if sort_order == 'desc':
            order_by = order_by.desc()

        query = query.order_by(order_by)
        return query.offset(skip).limit(limit).all()

    def _validate_member_addition(
        self,
        group: models.Group,
        citizen_id: int,
        application: Optional[Application] = None,
    ) -> None:
        """Validate if a citizen can be added to a group"""
        # members_ids = [member.id for member in group.members]
        # if citizen_id in members_ids:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail='Citizen already in group',
        #     )

        leaders_ids = [leader.id for leader in group.leaders]
        if citizen_id in leaders_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Citizen is a leader',
            )

        if group.max_members is not None and len(group.members) >= group.max_members:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Group is full',
            )

        # if application and application.group_id:
        #     err_msg = (
        #         'Citizen already has an application in this group'
        #         if application.group_id == group.id
        #         else 'Citizen already has an application in another group'
        #     )
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=err_msg,
        #     )

    def _get_by_slug(self, db: Session, slug: str) -> models.Group:
        group = db.query(self.model).filter(self.model.slug == slug).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Group not found',
            )
        return group

    def add_member(
        self,
        db: Session,
        group_id: Union[int, str],
        member: schemas.GroupMember,
        user: TokenData,
    ) -> ApplicationWithAuth:
        try:
            group_id = int(group_id)
            group = self.get(db, group_id, user)
        except ValueError:
            group = self._get_by_slug(db, group_id)

        citizen = citizens_crud.get_or_create(
            db,
            CitizenCreate(
                primary_email=member.email,
                first_name=member.first_name,
                last_name=member.last_name,
            ),
        )

        application = applications_crud.get_by_citizen_and_popup_city(
            db, citizen.id, group.popup_city_id
        )

        self._validate_member_addition(group, citizen.id, application)

        if not application:
            application = applications_crud.create(
                db,
                ApplicationCreate(
                    citizen_id=citizen.id,
                    popup_city_id=group.popup_city_id,
                    group_id=group.id,
                    first_name=member.first_name,
                    last_name=member.last_name,
                ),
                user,
            )
        else:
            application.group_id = group.id
            db.refresh(application)

        group.members.append(citizen)
        db.commit()
        db.refresh(group)
        db.refresh(application)

        app = Application.model_validate(application)
        return ApplicationWithAuth(
            **app.model_dump(),
            authorization=citizen.get_authorization(),
        )

    def remove_member(
        self,
        db: Session,
        group_id: int,
        citizen_id: int,
        user: TokenData,
    ):
        group = self.get(db, group_id, user)
        application = applications_crud.get_by_citizen_and_popup_city(
            db, citizen_id, group.popup_city_id
        )
        if application:
            for payment in application.payments:
                if payment.group_id == group.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail='Cannot remove member with existing group payments',
                    )
            if application.created_by_leader:
                applications_crud.delete(db, application.id, user)
            else:
                application.group_id = None
                db.commit()
                db.refresh(application)

        group.members.remove(citizen_id)
        db.commit()
        db.refresh(group)
        return group

    def set_products(
        self,
        db: Session,
        group_id: int,
        products: List[int],
        user: TokenData,
    ):
        group = self.get(db, group_id, user)
        group.products = products
        db.commit()
        db.refresh(group)
        return group


group = CRUDGroup(models.Group)
