from typing import Generic, List, Optional, Type, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import Session

from app.core.logger import logger

ModelType = TypeVar('ModelType', bound=DeclarativeMeta)
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def create(self, db: Session, obj: CreateSchemaType) -> ModelType:
        """Create a new record."""
        try:
            db_obj = self.model(**obj.model_dump())
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            logger.error(f'Error creating {self.model.__name__}: {str(e)}')
            db.rollback()
            raise e

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """Get a single record by id."""
        obj = db.query(self.model).filter(self.model.id == id).first()
        if not obj:
            raise HTTPException(
                status_code=404, detail=f'{self.model.__name__} not found'
            )
        return obj

    def find(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get multiple records with pagination."""
        try:
            return db.query(self.model).offset(skip).limit(limit).all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def update(self, db: Session, id: int, obj: UpdateSchemaType) -> ModelType:
        """Update a record."""
        try:
            db_obj = self.get(db, id)  # This will raise 404 if not found
            obj_data = obj.dict(exclude_unset=True)

            for field, value in obj_data.items():
                setattr(db_obj, field, value)

            db.commit()
            db.refresh(db_obj)
            return db_obj
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def delete(self, db: Session, id: int) -> ModelType:
        """Delete a record."""
        try:
            obj = self.get(db, id)  # This will raise 404 if not found
            db.delete(obj)
            db.commit()
            return obj
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
