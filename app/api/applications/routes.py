from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.applications import schemas
from app.api.applications.crud import application as application_crud
from app.core.database import get_db
from app.core.security import TokenData, get_current_user

router = APIRouter()


@router.post(
    '/',
    response_model=schemas.Application,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    application: schemas.ApplicationCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return application_crud.create(db=db, obj=application)


@router.get('/', response_model=list[schemas.Application])
def get_applications(
    current_user: TokenData = Depends(get_current_user),
    filters: schemas.ApplicationFilter = Depends(),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return application_crud.find(db=db, skip=skip, limit=limit, filters=filters)


@router.get('/{application_id}', response_model=schemas.Application)
def get_application(
    application_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_application = application_crud.get(db=db, id=application_id)
    if db_application is None:
        raise HTTPException(status_code=404, detail='Application not found')
    return db_application


@router.put('/{application_id}', response_model=schemas.Application)
def update_application(
    application_id: int,
    application: schemas.ApplicationUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return application_crud.update(db=db, id=application_id, obj=application)
