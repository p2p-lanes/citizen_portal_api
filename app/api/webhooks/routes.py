from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.webhooks import schemas
from app.core.database import get_db

router = APIRouter()


@router.post('/send_email', status_code=status.HTTP_201_CREATED)
def send_email(
    webhook_payload: schemas.WebhookPayload,
    template: str = Query(..., description='Email template name'),
    fields: str = Query(..., description='Template fields'),
    pop_up_city: str = Query(..., description='Pop-up city name'),
    db: Session = Depends(get_db),
):
    # TODO: Implement email sending logic
    return {'message': 'Email sent successfully'}
