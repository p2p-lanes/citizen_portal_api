from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.applications import schemas
from app.api.applications.crud import application as application_crud
from app.core.database import get_db

router = APIRouter()


# Create a new application
@router.post(
    '/', response_model=schemas.Application, status_code=status.HTTP_201_CREATED
)
def create_application(
    application: schemas.ApplicationCreate, db: Session = Depends(get_db)
):
    return application_crud.create(db=db, obj=application)


# Get all applications
@router.get('/', response_model=list[schemas.Application])
def get_applications(
    filters: schemas.ApplicationFilter = Depends(),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return application_crud.find(db=db, skip=skip, limit=limit, filters=filters)


# Get application by ID
@router.get('/{application_id}', response_model=schemas.Application)
def get_application(application_id: UUID, db: Session = Depends(get_db)):
    db_application = application_crud.get(db=db, id=application_id)
    if db_application is None:
        raise HTTPException(status_code=404, detail='Application not found')
    return db_application


# Update application
@router.put('/{application_id}', response_model=schemas.Application)
def update_application(
    application_id: UUID,
    application: schemas.ApplicationUpdate,
    db: Session = Depends(get_db),
):
    return application_crud.update(db=db, id=application_id, obj=application)
