from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.api.attendees import schemas
from app.api.attendees.crud import attendee as attendee_crud
from app.core.config import settings
from app.core.database import get_db
from app.core.logger import logger

router = APIRouter()


# Search for attendees by email
@router.get('/search/email', response_model=list[schemas.Attendee])
def search_attendees_by_email(
    email: str,
    x_api_key: str = Header(...),
    db: Session = Depends(get_db),
):
    if x_api_key != settings.ATTENDEES_API_KEY:
        raise HTTPException(status_code=403, detail='Invalid API key')
    logger.info(f'Searching for attendees by email: {email}')
    attendees = attendee_crud.get_by_email(db=db, email=email)
    if not attendees:
        raise HTTPException(
            status_code=404, detail='No attendees found with this email'
        )
    return attendees
