from uuid import uuid4

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Citizen(Base):
    __tablename__ = 'citizens'

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, unique=True, index=True
    )
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, index=True)
