from uuid import uuid4

from sqlalchemy import Column, Float, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Product(Base):
    __tablename__ = 'products'

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, unique=True, index=True
    )
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
