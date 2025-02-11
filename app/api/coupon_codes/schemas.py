from pydantic import BaseModel, ConfigDict


class CouponCode(BaseModel):
    id: int
    code: str
    popup_city_id: int
    discount_value: float

    model_config = ConfigDict(
        from_attributes=True,
    )
