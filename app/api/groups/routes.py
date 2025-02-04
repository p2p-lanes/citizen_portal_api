from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.groups import schemas
from app.api.groups.crud import group as group_crud
from app.core.database import get_db
from app.core.security import TokenData, get_current_user

router = APIRouter()


@router.get('/', response_model=list[schemas.Group])
def get_groups(
    current_user: TokenData = Depends(get_current_user),
    filters: schemas.GroupFilter = Depends(),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    sort_by: str = Query(default='name', description='Field to sort by'),
    sort_order: str = Query(default='asc', pattern='^(asc|desc)$'),
    db: Session = Depends(get_db),
):
    return group_crud.find(
        db=db,
        skip=skip,
        limit=limit,
        filters=filters,
        user=current_user,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get('/{group_id}', response_model=schemas.Group)
def get_group(
    group_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return group_crud.get(db=db, id=group_id, user=current_user)
