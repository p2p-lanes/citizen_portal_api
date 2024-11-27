from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.products import schemas
from app.api.products.crud import product as product_crud
from app.core.database import get_db

router = APIRouter()


# Create a new product
@router.post('/', response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    return product_crud.create(db=db, obj=product)


# Get all products
@router.get('/', response_model=list[schemas.Product])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return product_crud.find(db=db, skip=skip, limit=limit)


# Get product by ID
@router.get('/{product_id}', response_model=schemas.Product)
def get_product(product_id: UUID, db: Session = Depends(get_db)):
    db_product = product_crud.get(db=db, id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail='Product not found')
    return db_product
