from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.citizens import schemas
from app.api.citizens.crud import citizen as citizen_crud
from app.core.database import get_db
from app.core.security import TokenData, get_current_user

router = APIRouter()


@router.post('/signup', response_model=schemas.Citizen)
def signup(
    citizen: schemas.CitizenCreate,
    db: Session = Depends(get_db),
):
    return citizen_crud.signup(db=db, obj=citizen)


@router.post('/authenticate')
def authenticate(
    data: schemas.Authenticate,
    db: Session = Depends(get_db),
):
    return citizen_crud.authenticate(
        db=db, email=data.email, popup_slug=data.popup_slug
    )


@router.post('/login')
def login(
    email: str,
    spice: str,
    db: Session = Depends(get_db),
):
    citizen = citizen_crud.login(db=db, email=email, spice=spice)
    return citizen.get_authorization()


# Get all citizens
@router.get('/', response_model=list[schemas.Citizen])
def get_citizens(
    current_user: TokenData = Depends(get_current_user),
    filters: schemas.CitizenFilter = Depends(),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return citizen_crud.find(
        db=db,
        skip=skip,
        limit=limit,
        filters=filters,
        user=current_user,
    )


# Get citizen by ID
@router.get('/{citizen_id}', response_model=schemas.Citizen)
def get_citizen(
    citizen_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return citizen_crud.get(db=db, id=citizen_id, user=current_user)


@router.get('/email/{email}', response_model=schemas.Citizen)
def get_citizen_by_email(
    email: str,
    db: Session = Depends(get_db),
):
    citizen = citizen_crud.get_by_email(db=db, email=email)
    if not citizen:
        raise HTTPException(status_code=404, detail='Citizen not found')
    return citizen
