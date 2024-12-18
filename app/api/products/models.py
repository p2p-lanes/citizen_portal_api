from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.api.applications.models import Application


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

    applications: Mapped[List['Application']] = relationship(
        'Application',
        secondary='application_products',
        back_populates='products',
        viewonly=True,
    )
    application_products = relationship('ApplicationProduct', back_populates='product')
    payment_products = relationship('PaymentProduct', back_populates='product')

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)
    updated_by = Column(String)
