from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class PaymentSource(str, Enum):
    SIMPLEFI = 'SimpleFI'
    STRIPE = 'Stripe'


class PaymentBase(BaseModel):
    application_id: int
    external_id: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[float] = None
    source: Optional[PaymentSource] = None
    currency: Optional[str] = None
    rate: Optional[float] = None
    checkout_url: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaymentProduct(BaseModel):
    product_id: int
    attendee_id: int
    quantity: int


class PaymentCreate(BaseModel):
    application_id: int
    products: List[PaymentProduct]

    @field_validator('products', mode='before')
    def validate_products(cls, v: List[PaymentProduct]) -> List[PaymentProduct]:
        if not v:
            raise ValueError('At least one product must be selected')
        return v


class InternalPaymentCreate(PaymentCreate, PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    status: Optional[str] = None
    currency: Optional[str] = None
    source: Optional[PaymentSource] = None
    rate: Optional[float] = None


class PaymentProductResponse(BaseModel):
    product_id: int
    attendee_id: int
    quantity: int
    product_name: str
    product_description: Optional[str]
    product_price: float
    product_category: str
    created_at: datetime


class Payment(PaymentBase):
    id: int
    products_snapshot: List[PaymentProductResponse]

    model_config = ConfigDict(
        from_attributes=True,
    )


class PaymentFilter(BaseModel):
    id: Optional[int] = None
    application_id: Optional[int] = None
    citizen_id: Optional[int] = None
    external_id: Optional[str] = None
