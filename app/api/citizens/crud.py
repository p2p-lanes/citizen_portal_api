from sqlalchemy.orm import Session

from app.api.citizens import models, schemas


# Create a new citizen
def create_citizen(db: Session, citizen: schemas.CitizenCreate):
    db_citizen = models.Citizen(**citizen.dict())
    db.add(db_citizen)
    db.commit()
    db.refresh(db_citizen)
    return db_citizen


# Get all citizens
def get_citizens(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Citizen).offset(skip).limit(limit).all()


# Get citizen by ID
def get_citizen(db: Session, citizen_id: int):
    return db.query(models.Citizen).filter(models.Citizen.id == citizen_id).first()


# Update citizen
def update_citizen(db: Session, citizen_id: int, citizen: schemas.CitizenCreate):
    db_citizen = (
        db.query(models.Citizen).filter(models.Citizen.id == citizen_id).first()
    )
    if db_citizen:
        db_citizen.name = citizen.name
        db_citizen.description = citizen.description
        db_citizen.price = citizen.price
        db.commit()
        db.refresh(db_citizen)
    return db_citizen


# Delete citizen
def delete_citizen(db: Session, citizen_id: int):
    db_citizen = (
        db.query(models.Citizen).filter(models.Citizen.id == citizen_id).first()
    )
    if db_citizen:
        db.delete(db_citizen)
        db.commit()
    return db_citizen
