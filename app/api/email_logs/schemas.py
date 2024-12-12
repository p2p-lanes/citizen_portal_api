import json
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_serializer


class EmailLogFilter(BaseModel):
    receiver_email: Optional[str] = None
    template: Optional[str] = None
    status: Optional[str] = None
    params: Optional[dict] = None

    @field_serializer('params')
    def serialize_params(self, params: Optional[dict]) -> Optional[str]:
        if params is None or not params:
            return None
        return json.dumps(params, sort_keys=True)


class EmailLogBase(BaseModel):
    receiver_email: str
    template: str
    params: dict
    status: str
    error_message: Optional[str] = None
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
