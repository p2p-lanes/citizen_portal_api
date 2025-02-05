from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)

from app.core.database import Base
from app.core.utils import current_time


class CouponCode(Base):
    __tablename__ = 'coupon_codes'
    __table_args__ = (
        UniqueConstraint('code', 'popup_city_id', name='uix_code_popup_city'),
    )

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        index=True,
    )
    code = Column(String, index=True)
    popup_city_id = Column(Integer, ForeignKey('popups.id'), index=True, nullable=False)
    discount_value = Column(Float)
    max_uses = Column(Integer)
    current_uses = Column(Integer, default=0)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=current_time)
    updated_at = Column(DateTime, default=current_time, onupdate=current_time)
    created_by = Column(String)
    updated_by = Column(String)
