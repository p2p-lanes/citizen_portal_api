from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.organizations import crud as organization
from app.api.organizations import schemas
from app.core.database import get_db
from app.core.security import TokenData, get_current_user

router = APIRouter()


@router.get('/organizations', response_model=list[schemas.Organization])
def get_organizations(
    skip: int = 0,
    limit: int = 100,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return organization.find(db=db, skip=skip, limit=limit)
