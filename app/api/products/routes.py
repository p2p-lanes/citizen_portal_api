from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.products import schemas
from app.api.products.crud import product as product_crud
from app.core.config import settings
from app.core.database import get_db
from app.core.security import SYSTEM_TOKEN, TokenData, get_current_user

router = APIRouter()


@router.get('/', response_model=list[schemas.Product])
def get_products(
    current_user: TokenData = Depends(get_current_user),
    filters: schemas.ProductFilter = Depends(),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    sort_by: str = Query(default='name', description='Field to sort by'),
    sort_order: str = Query(default='asc', pattern='^(asc|desc)$'),
    db: Session = Depends(get_db),
):
    return product_crud.find(
        db=db,
        skip=skip,
        limit=limit,
        filters=filters,
        user=current_user,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get('/fast_checkout', response_model=list[schemas.Product])
def get_products_fast_checkout(
    api_key: str = Header(None, alias='api-key'),
    filters: schemas.ProductFilter = Depends(),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    sort_by: str = Query(default='name', description='Field to sort by'),
    sort_order: str = Query(default='asc', pattern='^(asc|desc)$'),
    db: Session = Depends(get_db),
):
    if api_key != settings.FAST_CHECKOUT_API_KEY:
        raise HTTPException(status_code=401, detail='Unauthorized')

    return product_crud.find(
        db=db,
        skip=skip,
        limit=limit,
        filters=filters,
        user=SYSTEM_TOKEN,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get('/{product_id}', response_model=schemas.Product)
def get_product(
    product_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return product_crud.get(db=db, id=product_id, user=current_user)
