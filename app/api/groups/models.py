from typing import TYPE_CHECKING, List

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app.api.popup_city.models import PopUpCity
from app.core.database import Base
from app.core.utils import current_time

if TYPE_CHECKING:
    from app.api.applications.models import Application
    from app.api.citizens.models import Citizen
    from app.api.products.models import Product


class GroupLeader(Base):
    __tablename__ = 'group_leaders'

    citizen_id = Column(Integer, ForeignKey('humans.id'), primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), primary_key=True)


class GroupMembers(Base):
    __tablename__ = 'group_members'

    citizen_id = Column(Integer, ForeignKey('humans.id'), primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), primary_key=True)


class GroupProducts(Base):
    __tablename__ = 'group_products'

    group_id = Column(Integer, ForeignKey('groups.id'), primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)


class Group(Base):
    __tablename__ = 'groups'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        index=True,
    )
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    discount_percentage = Column(Float, nullable=False)
    popup_city_id = Column(Integer, ForeignKey('popups.id'), index=True, nullable=False)
    max_members = Column(Integer)

    created_at = Column(DateTime, default=current_time)
    updated_at = Column(DateTime, default=current_time, onupdate=current_time)
    created_by = Column(String)
    updated_by = Column(String)

    applications: Mapped[List['Application']] = relationship(
        'Application', back_populates='group'
    )
    leaders: Mapped[List['Citizen']] = relationship(
        'Citizen', secondary='group_leaders', backref='led_groups'
    )
    members: Mapped[List['Citizen']] = relationship(
        'Citizen', secondary='group_members', back_populates='groups_as_member'
    )
    products: Mapped[List['Product']] = relationship(
        'Product', secondary='group_products', backref='groups'
    )
    popup_city: Mapped['PopUpCity'] = relationship('PopUpCity', lazy='joined')

    @property
    def popup_name(self) -> str:
        return self.popup_city.name

    def is_leader(self, citizen_id: int) -> bool:
        return any(leader.id == citizen_id for leader in self.leaders)
