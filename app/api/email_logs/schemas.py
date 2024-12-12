from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EmailLogBase(BaseModel):
    receiver_email: str
    template: str
    params: str
    status: str
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None


class EmailLogCreate(EmailLogBase):
    pass


class EmailLog(EmailLogBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True,
    )
