from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ProductBase(BaseModel):
    name: str
    price: float
    popup_city_id: int
    description: Optional[str] = None
    category: Optional[str] = None
    attendee_category: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = True

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProductCreate(ProductBase):
    name: Optional[str] = None


class ProductUpdate(ProductBase):
    pass


class Product(ProductBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class ProductFilter(BaseModel):
    id: Optional[int] = None
    id_in: Optional[List[int]] = None
    is_active: Optional[bool] = None
    name: Optional[str] = None
    category: Optional[str] = None
    popup_city_id: Optional[int] = None
