from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.attendees import schemas
from app.api.attendees.crud import attendee as attendee_crud
from app.core.config import settings
from app.core.database import get_db
from app.core.logger import logger
from app.core.security import TokenData, get_current_user

router = APIRouter()


# Create a new attendee
@router.post('/', response_model=schemas.Attendee)
def create_attendee(
    attendee: schemas.InternalAttendeeCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    logger.info('Creating attendee: %s', attendee)
    return attendee_crud.create(db=db, obj=attendee, user=current_user)


# Get all attendees
@router.get('/', response_model=list[schemas.Attendee])
def get_attendees(
    filters: schemas.AttendeeFilter = Depends(),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    return attendee_crud.find(
        db=db, filters=filters, skip=skip, limit=limit, user=current_user
    )


# Get attendee by ID
@router.get('/{attendee_id}', response_model=schemas.Attendee)
def get_attendee(
    attendee_id: int,
    db: Session = Depends(get_db),
):
    attendee = attendee_crud.get(db=db, id=attendee_id)
    if not attendee:
        raise HTTPException(status_code=404, detail='Attendee not found')
    return attendee


# Update an attendee
@router.put('/{attendee_id}', response_model=schemas.Attendee)
def update_attendee(
    attendee_id: int,
    attendee: schemas.AttendeeUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    logger.info('Updating attendee: %s: %s', attendee_id, attendee)
    updated_attendee = attendee_crud.update(db=db, id=attendee_id, obj=attendee)
    if not updated_attendee:
        raise HTTPException(status_code=404, detail='Attendee not found')
    return updated_attendee


# Delete an attendee
@router.delete('/{attendee_id}', response_model=dict)
def delete_attendee(
    attendee_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    logger.info('Deleting attendee: %s', attendee_id)
    result = attendee_crud.delete(db=db, id=attendee_id)
    if not result:
        raise HTTPException(status_code=404, detail='Attendee not found')
    return {'detail': 'Attendee deleted successfully'}


# Search for attendees by email
@router.get('/search/email', response_model=list[schemas.Attendee])
def search_attendees_by_email(
    email: str,
    x_api_key: str = Header(...),
    db: Session = Depends(get_db),
):
    if x_api_key != settings.ATTENDEES_API_KEY:
        raise HTTPException(status_code=403, detail='Invalid API key')
    attendees = attendee_crud.get_by_email(db=db, email=email)
    if not attendees:
        raise HTTPException(
            status_code=404, detail='No attendees found with this email'
        )
    return attendees
