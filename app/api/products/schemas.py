from pydantic import BaseModel
from uuid import UUID


class ProductBase(BaseModel):
    name: str
    description: str
    price: float


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: UUID

    class Config:
        from_attributes = True  # Allows Pydantic models to read SQLAlchemy models
