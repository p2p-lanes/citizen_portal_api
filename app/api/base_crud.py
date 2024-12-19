from typing import Generic, List, Optional, Type, TypeVar

import psycopg2
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import Query, Session

from app.core.logger import logger
from app.core.security import TokenData

ModelType = TypeVar('ModelType', bound=DeclarativeMeta)
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def _check_permission(self, db_obj: ModelType, user: TokenData) -> bool:
        """Override this method to implement permission checks"""
        return True

    def _apply_filters(
        self, query: Query, filters: Optional[BaseModel] = None
    ) -> Query:
        """Override this method to implement filter logic"""
        if not filters:
            return query

        for field, value in filters.model_dump(exclude_none=True).items():
            op = 'eq'
            if field.endswith('_in') and isinstance(value, list):
                field = field[:-3]
                op = 'in_'
            if hasattr(self.model, field) and value is not None:
                if op == 'in_':
                    query = query.filter(getattr(self.model, field).in_(value))
                else:
                    query = query.filter(getattr(self.model, field) == value)
        return query

    def create(
        self,
        db: Session,
        obj: CreateSchemaType,
        user: Optional[TokenData] = None,
    ) -> ModelType:
        """Create a new record."""
        try:
            # Convert to dict and filter out relationship fields that aren't direct columns
            obj_data = obj.model_dump()
            model_columns = self.model.__table__.columns.keys()
            filtered_data = {k: v for k, v in obj_data.items() if k in model_columns}

            db_obj = self.model(**filtered_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            logger.error('Error creating %s: %s', self.model.__name__, str(e))
            db.rollback()
            orig = str(e.orig)
            detail = 'Integrity error'
            if orig and orig.find('DETAIL') != -1:
                detail = orig.split('DETAIL: ')[1].split('\n')[0].strip()
            logger.error('Integrity error: %s', detail)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=detail,
            )
        except Exception as e:
            logger.error('Error creating %s: %s', self.model.__name__, str(e))
            db.rollback()
            raise e

    def get(self, db: Session, id: int, user: TokenData) -> ModelType:
        """Get a single record by id with permission check."""
        obj = db.query(self.model).filter(self.model.id == id).first()
        if not obj:
            logger.error('Record not found')
            raise HTTPException(
                status_code=404, detail=f'{self.model.__name__} not found'
            )
        if not self._check_permission(obj, user):
            logger.error('Not authorized to access this resource')
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Not authorized to access this resource',
            )
        return obj

    def find(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[BaseModel] = None,
        user: Optional[TokenData] = None,
        sort_by: str = 'created_at',
        sort_order: str = 'desc',
    ) -> List[ModelType]:
        """Get multiple records with pagination, filters, sorting and permission check."""
        query = db.query(self.model)
        query = self._apply_filters(query, filters)

        # Validate sort field exists
        if not hasattr(self.model, sort_by):
            raise HTTPException(
                status_code=400, detail=f'Invalid sort field: {sort_by}'
            )

        # Apply sorting
        order_by = getattr(self.model, sort_by)
        if sort_order == 'desc':
            order_by = order_by.desc()

        query = query.order_by(order_by)
        return query.offset(skip).limit(limit).all()

    def update(
        self,
        db: Session,
        id: int,
        obj: UpdateSchemaType,
        user: TokenData,
    ) -> ModelType:
        """Update a record."""
        try:
            db_obj = self.get(db, id, user)  # This will raise 404 if not found
            obj_data = obj.dict(exclude_unset=True)

            for field, value in obj_data.items():
                setattr(db_obj, field, value)

            db.commit()
            db.refresh(db_obj)
            return db_obj
        except HTTPException as e:
            logger.error('HTTPException in update: %s', e)
            raise
        except Exception as e:
            logger.error('Exception in update: %s', e)
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def delete(self, db: Session, id: int, user: TokenData) -> ModelType:
        """Delete a record."""
        try:
            obj = self.get(db, id, user)  # This will raise 404 if not found
            db.delete(obj)
            db.commit()
            return obj
        except IntegrityError as e:
            db.rollback()
            logger.error('IntegrityError in delete: %s', e)

            if isinstance(e.orig, psycopg2.errors.ForeignKeyViolation):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail='Cannot delete this record because it is referenced by other records',
                )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Database integrity error occurred',
            )
