from pydantic import BaseModel, ConfigDict, field_validator


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
    discount_value: int
    max_uses: int
    is_active: bool = True

    @field_validator('discount_value')
    def validate_discount_value(cls, v: int) -> int:
        if v < 0 or v > 100 or v % 10 != 0:
            raise ValueError('discount_value must be 0, 10, 20, ..., 90, or 100')
        return v
