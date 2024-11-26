from sqlalchemy.orm import Session

from app.api.applications import models, schemas


# Create a new application
def create_application(db: Session, application: schemas.ApplicationCreate):
    db_application = models.Application(**application.dict())
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application


# Get all applications
def get_applications(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Application).offset(skip).limit(limit).all()


# Get application by ID
def get_application(db: Session, application_id: int):
    return (
        db.query(models.Application)
        .filter(models.Application.id == application_id)
        .first()
    )


# Update application
def update_application(
    db: Session, application_id: int, application: schemas.ApplicationCreate
):
    db_application = (
        db.query(models.Application)
        .filter(models.Application.id == application_id)
        .first()
    )
    if db_application:
        db_application.first_name = application.first_name
        db_application.last_name = application.last_name
        db_application.email = application.email
        db_application.telegram_username = application.telegram_username
        db_application.organization = application.organization
        db_application.role = application.role

        db.refresh(db_application)
    return db_application


# Delete application
def delete_application(db: Session, application_id: int):
    db_application = (
        db.query(models.Application)
        .filter(models.Application.id == application_id)
        .first()
    )
    if db_application:
        db.delete(db_application)
        db.commit()
    return db_application
