from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.popup_city import schemas
from app.api.popup_city.crud import popup_city as popup_city_crud
from app.core.database import get_db

router = APIRouter()


# Create a new popup city
@router.post('/', response_model=schemas.PopUpCity, status_code=status.HTTP_201_CREATED)
def create_popup_city(
    popup_city: schemas.PopUpCityCreate, db: Session = Depends(get_db)
):
    return popup_city_crud.create(db=db, obj=popup_city)


# Get all popup cities
@router.get('/', response_model=list[schemas.PopUpCity])
def get_popup_cities(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return popup_city_crud.find(db=db, skip=skip, limit=limit)


# Get popup city by ID
@router.get('/{popup_city_id}', response_model=schemas.PopUpCity)
def get_popup_city(popup_city_id: UUID, db: Session = Depends(get_db)):
    db_popup_city = popup_city_crud.get(db=db, id=popup_city_id)
    if db_popup_city is None:
        raise HTTPException(status_code=404, detail='Popup city not found')
    return db_popup_city
