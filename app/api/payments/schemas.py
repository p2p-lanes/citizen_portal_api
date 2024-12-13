from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class PaymentBase(BaseModel):
    products: List[int]
    products_data: List[str]
    application_id: int
    citizen_id: int
    external_id: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    checkout_url: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaymentCreate(BaseModel):
    application_id: int
    products: List[int]

    @field_validator('products', mode='before')
    def validate_products(cls, v: List[int]) -> List[int]:
        if not v:
            raise ValueError('At least one product must be selected')
        return v


class InternalPaymentCreate(PaymentCreate, PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    status: Optional[str] = None
    currency: Optional[str] = None


class Payment(PaymentBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class PaymentFilter(BaseModel):
    id: Optional[int] = None
    application_id: Optional[int] = None
    external_id: Optional[str] = None
