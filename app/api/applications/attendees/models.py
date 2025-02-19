from typing import TYPE_CHECKING, List

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base
from app.core.utils import current_time

if TYPE_CHECKING:
    from app.api.applications.models import Application
    from app.api.payments.models import PaymentProduct
    from app.api.products.models import Product


class AttendeeProduct(Base):
    __tablename__ = 'attendee_products'

    attendee_id = Column(Integer, ForeignKey('attendees.id'), primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)
    quantity = Column(Integer, nullable=False, default=1)

    attendee: Mapped['Attendee'] = relationship(
        'Attendee', back_populates='attendee_products'
    )
    product: Mapped['Product'] = relationship(
        'Product', back_populates='attendee_products'
    )


class Attendee(Base):
    __tablename__ = 'attendees'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        index=True,
    )
    application_id = Column(Integer, ForeignKey('applications.id'), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    email = Column(String)

    application: Mapped['Application'] = relationship(
        'Application', back_populates='attendees'
    )
    attendee_products: Mapped[List['AttendeeProduct']] = relationship(
        'AttendeeProduct', back_populates='attendee'
    )
    products: Mapped[List['Product']] = relationship(
        'Product',
        secondary='attendee_products',
        back_populates='attendees',
        overlaps='attendee_products,attendee,product',
    )
    payment_products: Mapped[List['PaymentProduct']] = relationship(
        'PaymentProduct', back_populates='attendee'
    )

    created_at = Column(DateTime, default=current_time)
    updated_at = Column(DateTime, default=current_time, onupdate=current_time)
