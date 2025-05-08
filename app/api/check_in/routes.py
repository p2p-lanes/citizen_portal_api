from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.api.check_in import schemas
from app.api.check_in.crud import check_in as check_in_crud
from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


@router.post('/qr', response_model=schemas.CheckInResponse)
def new_qr_check_in(
    check_in: schemas.NewQRCheckIn,
    x_api_key: str = Header(...),
    db: Session = Depends(get_db),
):
    if x_api_key != settings.CHECK_IN_API_KEY:
        raise HTTPException(status_code=403, detail='Invalid API key')
    return check_in_crud.new_qr_check_in(
        db=db,
        code=check_in.code,
    )


@router.post('/virtual', response_model=schemas.CheckInResponse)
def new_virtual_check_in(
    check_in: schemas.NewVirtualCheckIn,
    x_api_key: str = Header(...),
    db: Session = Depends(get_db),
):
    if x_api_key != settings.CHECK_IN_API_KEY:
        raise HTTPException(status_code=403, detail='Invalid API key')
    return check_in_crud.new_virtual_check_in(
        db=db,
        obj=check_in,
    )
