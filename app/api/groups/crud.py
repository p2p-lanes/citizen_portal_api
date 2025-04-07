from typing import List, Optional, Union

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.applications.crud import application as applications_crud
from app.api.applications.models import Application as ApplicationModel
from app.api.applications.schemas import (
    Application,
    ApplicationCreate,
    ApplicationStatus,
)
from app.api.base_crud import CRUDBase
from app.api.citizens.crud import citizen as citizens_crud
from app.api.citizens.schemas import CitizenCreate
from app.api.groups import models, schemas
from app.core.logger import logger
from app.core.security import SYSTEM_TOKEN, TokenData
from app.core.utils import current_time


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
        members_ids = [member.id for member in group.members]
        if citizen_id in members_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Citizen is already a member',
            )

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

        # Check for duplicate email in the group
        member_emails = [member.primary_email for member in group.members]
        if application and application.email in member_emails:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Email is already in use in this group',
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

    def get_by_slug(self, db: Session, slug: str) -> models.Group:
        group = db.query(self.model).filter(self.model.slug == slug).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Group not found',
            )
        return group

    def get_with_members(
        self, db: Session, id: int, user: TokenData
    ) -> schemas.GroupWithMembers:
        group = super().get(db, id, user)
        members = []
        for member in group.members:
            application = member.get_application(group.popup_city_id)
            products = []
            for attendee in application.attendees:
                products.extend(attendee.products)

            group_member = schemas.MemberWithProducts(
                id=member.id,
                first_name=application.first_name,
                last_name=application.last_name,
                email=application.email,
                telegram=application.telegram,
                organization=application.organization,
                role=application.role,
                gender=application.gender,
                products=products,
            )
            members.append(group_member)

        return schemas.GroupWithMembers(
            **schemas.Group.model_validate(group).model_dump(),
            members=members,
        )

    def add_member(
        self,
        db: Session,
        group_id: Union[int, str],
        member: schemas.GroupMember,
        user: TokenData,
    ) -> ApplicationModel:
        try:
            group_id = int(group_id)
            group = self.get(db, group_id, user)
        except ValueError:
            group = self.get_by_slug(db, group_id)

        citizen = citizens_crud.get_or_create(
            db,
            CitizenCreate(
                primary_email=member.email,
                first_name=member.first_name,
                last_name=member.last_name,
                gender=member.gender,
                role=member.role,
                telegram=member.telegram,
            ),
        )

        application = next(
            (a for a in citizen.applications if a.group_id == group.id), None
        )

        self._validate_member_addition(group, citizen.id, application)

        if not application:
            new_application = ApplicationCreate(
                citizen_id=citizen.id,
                popup_city_id=group.popup_city_id,
                group_id=group.id,
                first_name=member.first_name,
                last_name=member.last_name,
                role=member.role,
                organization=member.organization,
                gender=member.gender,
                telegram=member.telegram,
            )
            logger.info('Application not found, creating: %s', new_application)
            application = applications_crud.create(db, new_application, user)
        else:
            logger.info('Application found, updating: %s', application.id)
            application.group_id = group.id
            application.status = ApplicationStatus.ACCEPTED
            application.first_name = member.first_name
            application.last_name = member.last_name
            application.role = member.role
            application.organization = member.organization
            application.gender = member.gender
            application.telegram = member.telegram
            application.submitted_at = current_time()
            applications_crud.update_citizen_profile(db, application)

        if citizen.id not in [m.id for m in group.members]:
            group.members.append(citizen)
            logger.info('Citizen added to group: %s', citizen.id)

        db.commit()
        db.refresh(group)
        db.refresh(application)
        return application

    def create_member(
        self,
        db: Session,
        group_id: int,
        member: schemas.GroupMember,
        user: TokenData,
    ) -> schemas.MemberWithProducts:
        application = self.add_member(db, group_id, member, user)
        return schemas.MemberWithProducts(
            id=application.citizen_id,
            products=application.get_products(),
            first_name=application.first_name,
            last_name=application.last_name,
            email=application.email,
            telegram=application.telegram,
            organization=application.organization,
            role=application.role,
            gender=application.gender,
        )

    def create_members_batch(
        self,
        db: Session,
        group_id: int,
        members: List[schemas.GroupMember],
        user: TokenData,
    ) -> List[schemas.MemberBatchResult]:
        """Create multiple members in a group at once, handling partial success"""
        results = []

        for member in members:
            try:
                created_member = self.create_member(db, group_id, member, user)
                # Convert MemberWithProducts to MemberBatchResult
                result = schemas.MemberBatchResult(
                    **created_member.model_dump(), success=True, err_msg=None
                )
                results.append(result)
                db.commit()
            except HTTPException as e:
                if e.status_code == status.HTTP_403_FORBIDDEN:
                    logger.warning(
                        'User %s does not have permission to add member %s to group %s',
                        user.citizen_id,
                        member.email,
                        group_id,
                    )
                    db.rollback()
                    raise e

                # Create error result for this member
                result = schemas.MemberBatchResult(
                    id=0,  # Use 0 as a placeholder for failed creation
                    products=[],
                    success=False,
                    err_msg=str(e.detail),
                    **member.model_dump(),
                )
                results.append(result)
                db.rollback()  # Rollback only this member's transaction
            except Exception as e:
                db.rollback()  # Rollback only this member's transaction
                logger.error(
                    'Error creating member %s: %s',
                    member.email,
                    str(e),
                    exc_info=True,
                )
                raise e

        return results

    def _validate_member_exists(
        self,
        group: models.Group,
        citizen_id: int,
    ) -> None:
        """Validate that a citizen is a member of the group"""
        if citizen_id not in [m.id for m in group.members]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Member not found in group',
            )

    def update_member(
        self,
        db: Session,
        group_id: int,
        citizen_id: int,
        member: schemas.GroupMember,
        user: TokenData,
    ) -> schemas.MemberWithProducts:
        """Update a member's information in a group"""
        group = self.get(db, group_id, user)

        self._validate_member_exists(group, citizen_id)

        citizen = citizens_crud.get(db, citizen_id, SYSTEM_TOKEN)
        citizen.first_name = member.first_name
        citizen.last_name = member.last_name
        citizen.primary_email = member.email

        application = next(
            (a for a in citizen.applications if a.group_id == group_id), None
        )

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Application not found',
            )

        application.first_name = member.first_name
        application.last_name = member.last_name
        application.email = member.email
        application.role = member.role
        application.organization = member.organization
        application.gender = member.gender
        application.telegram = member.telegram
        application.submitted_at = current_time()

        db.commit()
        db.refresh(citizen)
        db.refresh(application)

        return schemas.MemberWithProducts(
            id=citizen.id,
            products=application.get_products(),
            first_name=application.first_name,
            last_name=application.last_name,
            email=application.email,
        )

    def remove_member(
        self,
        db: Session,
        group_id: int,
        citizen_id: int,
        user: TokenData,
    ):
        group = self.get(db, group_id, user)

        self._validate_member_exists(group, citizen_id)
        citizen = citizens_crud.get(db, citizen_id, SYSTEM_TOKEN)

        application = next(
            (a for a in citizen.applications if a.group_id == group.id), None
        )
        if application:
            if application.get_products():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Cannot remove member with products',
                )
            if application.created_by_leader:
                applications_crud.delete(db, application.id, user)
            else:
                application.group_id = None
                db.commit()
                db.refresh(application)

        group.members.remove(citizen)
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
