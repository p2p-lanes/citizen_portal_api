from pydantic import BaseModel, ConfigDict


class CouponCode(BaseModel):
    id: int
    code: str
    popup_city_id: int
    discount_value: float

    model_config = ConfigDict(
        from_attributes=True,
    )


class CouponCodeCreate(BaseModel):
    code: str
    popup_city_id: int
    discount_value: float
    max_uses: int
    current_uses: int
    is_active: bool = True
