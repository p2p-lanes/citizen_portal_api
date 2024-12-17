from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.api.applications.models import Application
    from app.api.products.models import Product


payment_products = Table(
    'payment_products',
    Base.metadata,
    Column('payment_id', Integer, ForeignKey('payments.id'), primary_key=True),
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True),
    # Snapshot of product data at time of purchase
    Column('product_name', String),
    Column('product_description', String, nullable=True),
    Column('product_price', Float),
    Column('product_category', String),
    Column('quantity', Integer, default=1),
    Column('created_at', DateTime, default=datetime.utcnow),
)


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
    products: Mapped[List['Product']] = relationship(
        'Product', secondary=payment_products, back_populates='payments'
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
