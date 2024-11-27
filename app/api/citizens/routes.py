from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.citizens import schemas
from app.api.citizens.crud import citizen as citizen_crud
from app.core.database import get_db

router = APIRouter()


# Create a new citizen
@router.post('/', response_model=schemas.Citizen)
def create_citizen(citizen: schemas.CitizenCreate, db: Session = Depends(get_db)):
    return citizen_crud.create(db=db, obj=citizen)


@router.post('/signup', response_model=schemas.Citizen)
def signup(citizen: schemas.CitizenCreate, db: Session = Depends(get_db)):
    return citizen_crud.signup(db=db, obj=citizen)


# Get all citizens
@router.get('/', response_model=list[schemas.Citizen])
def get_citizens(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return citizen_crud.find(db=db, skip=skip, limit=limit)


# Get citizen by ID
@router.get('/{citizen_id}', response_model=schemas.Citizen)
def get_citizen(citizen_id: UUID, db: Session = Depends(get_db)):
    db_citizen = citizen_crud.get(db=db, id=citizen_id)
    if db_citizen is None:
        raise HTTPException(status_code=404, detail='Citizen not found')
    return db_citizen
