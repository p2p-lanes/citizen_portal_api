from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.citizens import schemas
from app.api.citizens.crud import citizen as citizen_crud
from app.core.database import get_db

router = APIRouter()


# Create a new citizen
@router.post('/', response_model=schemas.Citizen, status_code=status.HTTP_201_CREATED)
def create_citizen(citizen: schemas.CitizenCreate, db: Session = Depends(get_db)):
    return citizen_crud.create(db=db, obj=citizen)


@router.post('/signup', response_model=schemas.Citizen)
def signup(citizen: schemas.CitizenCreate, db: Session = Depends(get_db)):
    return citizen_crud.signup(db=db, obj=citizen)


@router.get('/authenticate')
def authenticate(email: str, db: Session = Depends(get_db)):
    return citizen_crud.authenticate(db=db, email=email)


@router.post('/login')
def login(
    email: str,
    spice: str,
    db: Session = Depends(get_db),
):
    return citizen_crud.login(db=db, email=email, spice=spice)


# Get all citizens
@router.get('/', response_model=list[schemas.Citizen])
def get_citizens(
    filters: schemas.CitizenFilter = Depends(),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return citizen_crud.find(db=db, skip=skip, limit=limit, filters=filters)


# Get citizen by ID
@router.get('/{citizen_id}', response_model=schemas.Citizen)
def get_citizen(citizen_id: UUID, db: Session = Depends(get_db)):
    db_citizen = citizen_crud.get(db=db, id=citizen_id)
    if db_citizen is None:
        raise HTTPException(status_code=404, detail='Citizen not found')
    return db_citizen
