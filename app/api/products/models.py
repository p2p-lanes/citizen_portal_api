from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app.api.applications.models import application_products
from app.api.payments.models import payment_products
from app.core.database import Base

if TYPE_CHECKING:
    from app.api.applications.models import Application
    from app.api.payments.models import Payment


class Product(Base):
    __tablename__ = 'products'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        index=True,
    )
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    popup_city_id = Column(Integer, ForeignKey('popups.id'), index=True, nullable=False)
    description = Column(String)
    category = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)

    payments: Mapped[List['Payment']] = relationship(
        'Payment', secondary=payment_products, back_populates='products'
    )
    applications: Mapped[List['Application']] = relationship(
        'Application', secondary=application_products, back_populates='products'
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)
    updated_by = Column(String)
