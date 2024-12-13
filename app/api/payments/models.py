from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, ARRAY

from app.core.database import Base


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
    citizen_id = Column(Integer, ForeignKey('citizens.id'), nullable=False)
    products = Column(ARRAY(Integer), nullable=False)
    products_data = Column(ARRAY(String), nullable=False)
    external_id = Column(String)
    status = Column(String)
    amount = Column(Float)
    currency = Column(String)
    checkout_url = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
