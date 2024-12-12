from typing import Union

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
