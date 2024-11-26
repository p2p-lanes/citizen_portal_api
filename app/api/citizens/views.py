from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.citizens import crud, schemas
from app.core.database import get_db

router = APIRouter()


# Create a new citizen
@router.post('/', response_model=schemas.Citizen)
def create_citizen(citizen: schemas.CitizenCreate, db: Session = Depends(get_db)):
    return crud.create_citizen(db=db, citizen=citizen)


# Get all citizens
@router.get('/', response_model=list[schemas.Citizen])
def get_citizens(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_citizens(db=db, skip=skip, limit=limit)


# Get citizen by ID
@router.get('/{citizen_id}', response_model=schemas.Citizen)
def get_citizen(citizen_id: UUID, db: Session = Depends(get_db)):
    db_citizen = crud.get_citizen(db=db, citizen_id=citizen_id)
    if db_citizen is None:
        raise HTTPException(status_code=404, detail='Citizen not found')
    return db_citizen
