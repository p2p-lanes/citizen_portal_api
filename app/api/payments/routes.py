from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.payments import schemas
from app.api.payments.crud import payment as payment_crud
from app.core.config import settings
from app.core.database import get_db
from app.core.security import SYSTEM_TOKEN, TokenData, get_current_user

router = APIRouter()


@router.get('/', response_model=list[schemas.Payment])
def get_payments(
    current_user: TokenData = Depends(get_current_user),
    filters: schemas.PaymentFilter = Depends(),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return payment_crud.find(
        db=db,
        skip=skip,
        limit=limit,
        filters=filters,
        user=current_user,
    )


@router.get('/{payment_id}', response_model=schemas.Payment)
def get_payment(
    payment_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return payment_crud.get(db=db, id=payment_id, user=current_user)


@router.post('/', response_model=schemas.Payment)
def create_payment(
    payment: schemas.PaymentCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return payment_crud.create(db=db, obj=payment, user=current_user)


@router.post('/fast_checkout', response_model=schemas.Payment)
def create_payment_fast_checkout(
    payment: schemas.PaymentCreate,
    api_key: str = Header(None, alias='api-key'),
    db: Session = Depends(get_db),
):
    if api_key != settings.FAST_CHECKOUT_API_KEY:
        raise HTTPException(status_code=401, detail='Unauthorized')
    return payment_crud.create(db=db, obj=payment, user=SYSTEM_TOKEN)
