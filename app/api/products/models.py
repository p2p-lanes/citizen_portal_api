from sqlalchemy import Column, Float, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text

from app.core.database import Base


class Product(Base):
    __tablename__ = 'products'

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text('uuid_generate_v4()'),
        unique=True,
        index=True,
    )
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    price = Column(Float)
