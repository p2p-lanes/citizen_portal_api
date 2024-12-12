from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base


class EmailLog(Base):
    __tablename__ = 'email_logs'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        index=True,
    )
    receiver_email = Column(String, nullable=False, index=True)
    template = Column(String, nullable=False)
    params = Column(String)  # JSON string of parameters
    status = Column(String)  # success, failed
    error_message = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)
    updated_by = Column(String)
