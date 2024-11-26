from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.applications import crud, schemas
from app.core.database import get_db

router = APIRouter()


# Create a new application
@router.post('/', response_model=schemas.Application)
def create_application(
    application: schemas.ApplicationCreate, db: Session = Depends(get_db)
):
    return crud.create_application(db=db, application=application)


# Get all applications
@router.get('/', response_model=list[schemas.Application])
def get_applications(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_applications(db=db, skip=skip, limit=limit)


# Get application by ID
@router.get('/{application_id}', response_model=schemas.Application)
def get_application(application_id: UUID, db: Session = Depends(get_db)):
    db_application = crud.get_application(db=db, application_id=application_id)
    if db_application is None:
        raise HTTPException(status_code=404, detail='Application not found')
    return db_application
