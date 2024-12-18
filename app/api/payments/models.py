from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.api.applications.models import Application


class PaymentProduct(Base):
    __tablename__ = 'payment_products'

    payment_id = Column(Integer, ForeignKey('payments.id'), primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)
    attendee_id = Column(Integer, ForeignKey('attendees.id'))
    quantity = Column(Integer, default=1)

    product_name = Column(String)
    product_description = Column(String, nullable=True)
    product_price = Column(Float)
    product_category = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    payment = relationship('Payment', back_populates='products')
    product = relationship('Product', back_populates='payment_products')


class Payment(Base):
    __tablename__ = 'payments'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        index=True,
    )
    application_id = Column(Integer, ForeignKey('applications.id'), nullable=False)
    external_id = Column(String)
    status = Column(String)
    amount = Column(Float)
    currency = Column(String)
    checkout_url = Column(String)

    application: Mapped['Application'] = relationship(
        'Application', back_populates='payments'
    )
    products: Mapped[List['PaymentProduct']] = relationship(
        'PaymentProduct', back_populates='payment'
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
