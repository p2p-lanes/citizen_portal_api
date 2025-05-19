import json
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class EmailStatus(str, Enum):
    SUCCESS = 'success'
    FAILED = 'failed'
    SCHEDULED = 'scheduled'
    CANCELLED = 'cancelled'


class EmailEvent(str, Enum):
    APPLICATION_RECEIVED = 'application-received'
    AUTH_CITIZEN_PORTAL = 'auth-citizen-portal'
    AUTH_CITIZEN_BY_CODE = 'auth-citizen-by-code'
    PAYMENT_CONFIRMED = 'payment-confirmed'
    EDIT_PASSES_CONFIRMED = 'edit-passes-confirmed'
    CHECK_IN = 'check-in'
    CHECK_IN_REMINDER = 'check-in-reminder'


class EmailLogFilter(BaseModel):
    receiver_email: Optional[str] = None
    template: Optional[str] = None
    status: Optional[EmailStatus] = None
    params: Optional[dict] = None

    @field_serializer('params')
    def serialize_params(self, params: Optional[dict]) -> Optional[str]:
        if params is None or not params:
            return None
        return json.dumps(params, sort_keys=True)


class EmailAttachment(BaseModel):
    name: str = Field(alias='Name')
    content_id: str = Field(alias='ContentID')
    content: str = Field(alias='Content')
    content_type: str = Field(alias='ContentType')

    model_config = ConfigDict(
        populate_by_name=True,
    )


class EmailLogBase(BaseModel):
    receiver_email: str
    template: str
    event: str
    params: dict
    status: EmailStatus
    send_at: Optional[datetime] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    error_message: Optional[str] = None
    popup_city_id: Optional[int] = None
    attachments: Optional[List[EmailAttachment]] = None
    created_at: Optional[datetime] = None

    @field_serializer('params')
    def serialize_params(self, params: dict) -> str:
        return json.dumps(params, sort_keys=True)


class EmailLogCreate(EmailLogBase):
    pass


class EmailLog(EmailLogBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True,
    )
