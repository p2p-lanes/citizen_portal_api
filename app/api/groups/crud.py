from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.applications.crud import application as applications_crud
from app.api.applications.schemas import ApplicationCreate
from app.api.applications.models import Application
from app.api.base_crud import CRUDBase
from app.api.citizens.crud import citizen as citizens_crud
from app.api.citizens.schemas import CitizenCreate
from app.api.groups import models, schemas
from app.core.security import TokenData


class CRUDGroup(CRUDBase[models.Group, schemas.GroupBase, schemas.GroupBase]):
    def _check_permission(self, db_obj: models.Group, user: TokenData) -> bool:
        """Check if user is a group leader for this group"""
        if not user:
            return False

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
        if citizen_id in group.members:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Citizen already in group',
            )
        if citizen_id in group.leaders:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Citizen is a leader',
            )

        if group.max_members and len(group.members) >= group.max_members:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Group is full',
            )

        if application and application.group_id:
            err_msg = (
                'Citizen already has an application in this group'
                if application.group_id == group.id
                else 'Citizen already has an application in another group'
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg,
            )

    def add_member(
        self,
        db: Session,
        group_id: int,
        member: schemas.GroupMember,
        user: TokenData,
    ):
        group = self.get(db, group_id, user)
        citizen = citizens_crud.get_by_email(db, member.email)
        if not citizen:
            citizen = citizens_crud.create(
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

        if application:
            application.group_id = group.id
            db.commit()
            db.refresh(application)
        else:
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

        group.members.append(citizen.id)
        db.commit()
        db.refresh(group)
        return group

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
