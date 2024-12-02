from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base


class PopUpCity(Base):
    __tablename__ = 'popups'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        index=True,
    )
    name = Column(String, index=True, nullable=False)
    tagline = Column(String)
    location = Column(String)
    image_url = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
