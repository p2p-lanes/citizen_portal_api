from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.popup_city import schemas
from app.api.popup_city.crud import popup_city as popup_city_crud
from app.core.database import get_db
from app.core.security import TokenData, get_current_user

router = APIRouter()


@router.post('/', response_model=schemas.PopUpCity, status_code=status.HTTP_201_CREATED)
def create_popup_city(
    popup_city: schemas.PopUpCityCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return popup_city_crud.create(db=db, obj=popup_city)


@router.get('/', response_model=list[schemas.PopUpCity])
def get_popup_cities(
    current_user: TokenData = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return popup_city_crud.find(db=db, skip=skip, limit=limit)


@router.get('/{popup_city_id}', response_model=schemas.PopUpCity)
def get_popup_city(
    popup_city_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_popup_city = popup_city_crud.get(db=db, id=popup_city_id)
    if db_popup_city is None:
        raise HTTPException(status_code=404, detail='Popup city not found')
    return db_popup_city
