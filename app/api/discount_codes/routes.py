from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.discount_codes import schemas
from app.api.discount_codes.crud import discount_code as discount_code_crud
from app.core.database import get_db
from app.core.security import TokenData, get_current_user

router = APIRouter()


@router.get('/', response_model=schemas.DiscountCode)
def get_discount_code(
    current_user: TokenData = Depends(get_current_user),
    code: str = Query(),
    popup_city_id: int = Query(),
    db: Session = Depends(get_db),
):
    return discount_code_crud.get_by_code(
        db=db,
        code=code,
        popup_city_id=popup_city_id,
    )
