from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict


class WebhookRow(BaseModel):
    id: Union[int, str]
    # Using a dynamic dict to accept any key-value pairs
    model_config = ConfigDict(extra='allow')


class WebhookData(BaseModel):
    table_id: str
    table_name: str
    rows: list[WebhookRow]


class WebhookPayload(BaseModel):
    type: str
    id: str
    data: WebhookData


# Simplefi Models


class CardPaymentModel(BaseModel):
    provider: str
    status: str
    coin: str = 'USD'


class PriceDetailsModel(BaseModel):
    currency: str
    final_amount: float
    rate: float


class TransactionModel(BaseModel):
    id: str
    coin: str
    chain_id: int
    status: str
    price_details: PriceDetailsModel


class PaymentInfo(BaseModel):
    coin: str
    hash: str
    amount: float
    paid_at: datetime


class PaymentRequestModel(BaseModel):
    id: str
    order_id: int
    amount: float
    amount_paid: float
    currency: str
    reference: dict
    status: str
    status_detail: str
    transactions: List[TransactionModel]
    card_payment: Optional[CardPaymentModel] = None
    payments: List[PaymentInfo]


class SimplefiDataModel(BaseModel):
    payment_request: PaymentRequestModel
    new_payment: Optional[Union[PaymentInfo, CardPaymentModel]] = None


class SimplefiWebhookPayload(BaseModel):
    id: str
    event_type: str
    entity_type: str
    entity_id: str
    data: SimplefiDataModel
