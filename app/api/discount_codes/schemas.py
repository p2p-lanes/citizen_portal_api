from pydantic import BaseModel, ConfigDict


class DiscountCode(BaseModel):
    id: int
    code: str
    popup_city_id: int
    discount_type: str
    discount_value: float

    model_config = ConfigDict(
        from_attributes=True,
    )
