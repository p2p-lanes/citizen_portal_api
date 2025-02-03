from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.base_crud import CRUDBase
from app.api.discount_codes import models, schemas
from app.core.utils import current_time


class CRUDDiscountCode(
    CRUDBase[models.DiscountCode, schemas.DiscountCode, schemas.DiscountCode]
):
    def get_by_code(self, db: Session, code: str, popup_city_id: int):
        discount_code = (
            db.query(models.DiscountCode)
            .filter(
                models.DiscountCode.code == code,
                models.DiscountCode.popup_city_id == popup_city_id,
            )
            .first()
        )
        if not discount_code:
            raise HTTPException(
                status_code=404,
                detail='Coupon code not found. Please, enter a valid coupon.',
            )
        if not discount_code.is_active:
            raise HTTPException(status_code=404, detail='Discount code is not active')

        if discount_code.start_date and discount_code.start_date > current_time():
            raise HTTPException(
                status_code=404, detail='Discount code has not started yet'
            )

        if discount_code.end_date and discount_code.end_date < current_time():
            raise HTTPException(status_code=404, detail='Discount code has expired')

        current_uses = discount_code.current_uses or 0
        if discount_code.max_uses and current_uses >= discount_code.max_uses:
            raise HTTPException(
                status_code=404,
                detail='Discount code has reached the maximum number of uses',
            )

        return discount_code

    def use_discount_code(self, db: Session, discount_code_id: int):
        discount_code = self.get(db, discount_code_id, user=None)
        current_uses = discount_code.current_uses or 0
        discount_code.current_uses = current_uses + 1
        db.commit()


discount_code = CRUDDiscountCode(models.DiscountCode)
