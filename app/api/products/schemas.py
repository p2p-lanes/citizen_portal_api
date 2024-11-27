from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ProductBase(BaseModel):
    name: str
    description: Optional[str]
    price: Optional[float]


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: UUID

    model_config = {
        'from_attributes': True  # Allows Pydantic models to read SQLAlchemy models
    }
