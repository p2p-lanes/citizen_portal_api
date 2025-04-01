from typing import Union

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.applications.schemas import ApplicationWithAuth
from app.api.groups import schemas
from app.api.groups.crud import group as group_crud
from app.core.config import settings
from app.core.database import get_db
from app.core.security import SYSTEM_TOKEN, TokenData, get_current_user

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


@router.get('/aux/{group_slug}', response_model=schemas.Group)
def get_group_aux(
    group_slug: str,
    api_key: str = Header(None, alias='api-key'),
    db: Session = Depends(get_db),
):
    if api_key != settings.GROUPS_API_KEY:
        raise HTTPException(status_code=401, detail='Unauthorized')
    return group_crud.get_by_slug(db=db, slug=group_slug)


@router.post('/{group_id}/new_member', response_model=ApplicationWithAuth)
def new_member(
    group_id: Union[int, str],
    member: schemas.GroupMember,
    api_key: str = Header(None, alias='api-key'),
    db: Session = Depends(get_db),
):
    if api_key != settings.GROUPS_API_KEY:
        raise HTTPException(status_code=401, detail='Unauthorized')

    return group_crud.add_member(
        db=db,
        group_id=group_id,
        member=member,
        user=SYSTEM_TOKEN,
    )
