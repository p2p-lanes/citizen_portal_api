from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.base_crud import CRUDBase
from app.api.organizations import models, schemas


class CRUDOrganization(
    CRUDBase[
        models.Organization, schemas.OrganizationCreate, schemas.OrganizationCreate
    ]
):
    def get_by_name(self, db: Session, name: str) -> Optional[models.Organization]:
        return (
            db.query(self.model)
            .filter(func.lower(self.model.name) == name.lower())
            .first()
        )

    def get_or_create(self, db: Session, name: str) -> models.Organization:
        organization = self.get_by_name(db, name)
        if not organization:
            organization = self.create(
                db,
                schemas.OrganizationCreate(name=name),
            )
        return organization


organization = CRUDOrganization(models.Organization)
