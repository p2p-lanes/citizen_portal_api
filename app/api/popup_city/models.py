from typing import List

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app.api.email_logs.schemas import EmailEvent
from app.core.database import Base
from app.core.utils import current_time


class EmailTemplate(Base):
    __tablename__ = 'popup_email_templates'

    id = Column(Integer, primary_key=True)
    popup_city_id = Column(Integer, ForeignKey('popups.id'), nullable=False)
    event = Column(String, nullable=False)
    template = Column(String, nullable=False)
    frequency = Column(String)
    created_at = Column(DateTime, default=current_time)
    updated_at = Column(DateTime, default=current_time, onupdate=current_time)

    popup_city: Mapped['PopUpCity'] = relationship(
        'PopUpCity', back_populates='templates'
    )


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
    slug = Column(String, index=True, nullable=False, unique=True)
    tagline = Column(String)
    location = Column(String)
    passes_description = Column(String)
    image_url = Column(String)
    web_url = Column(String)
    email_image = Column(String)
    contact_email = Column(String)
    blog_url = Column(String)
    twitter_url = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    allows_spouse = Column(Boolean, default=False)
    allows_children = Column(Boolean, default=False)
    allows_coupons = Column(Boolean, default=False)
    clickable_in_portal = Column(Boolean, nullable=True, default=False)
    visible_in_portal = Column(Boolean, nullable=True, default=False)
    requires_approval = Column(Boolean, nullable=False, default=True)
    auto_approval_time = Column(Integer, nullable=True)  # in minutes
    portal_order = Column(Float, nullable=False, default=0)
    simplefi_api_key = Column(String)

    templates: Mapped[List[EmailTemplate]] = relationship(
        'EmailTemplate', back_populates='popup_city'
    )

    created_at = Column(DateTime, default=current_time)
    updated_at = Column(DateTime, default=current_time, onupdate=current_time)
    created_by = Column(String)
    updated_by = Column(String)

    def get_email_template(self, event: EmailEvent) -> str:
        for t in self.templates:
            if t.event == event:
                return t.template
        raise ValueError(
            f'No template found for event: {event} (popup_city: {self.id} {self.name})'
        )
