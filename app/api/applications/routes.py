from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.applications import schemas
from app.api.applications.attendees import schemas as attendees_schemas
from app.api.applications.crud import application as application_crud
from app.core.database import get_db
from app.core.security import TokenData, get_current_user

router = APIRouter()


@router.post(
    '/',
    response_model=schemas.Application,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    application: schemas.ApplicationCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return application_crud.create(db=db, obj=application, user=current_user)


@router.get('/', response_model=list[schemas.Application])
def get_applications(
    current_user: TokenData = Depends(get_current_user),
    filters: schemas.ApplicationFilter = Depends(),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return application_crud.find(
        db=db,
        skip=skip,
        limit=limit,
        filters=filters,
        user=current_user,
    )


@router.get('/{application_id}', response_model=schemas.Application)
def get_application(
    application_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return application_crud.get(db=db, id=application_id, user=current_user)


@router.put('/{application_id}', response_model=schemas.Application)
def update_application(
    application_id: int,
    application: schemas.ApplicationUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return application_crud.update(
        db=db,
        id=application_id,
        obj=application,
        user=current_user,
    )


@router.put('/{application_id}/attendees', response_model=attendees_schemas.Attendee)
def create_attendee(
    application_id: int,
    attendee: attendees_schemas.AttendeeCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return application_crud.create_attendee(
        db=db,
        application_id=application_id,
        attendee=attendee,
        user=current_user,
    )


@router.put(
    '/{application_id}/attendees/{attendee_id}',
    response_model=attendees_schemas.Attendee,
)
def update_attendee(
    application_id: int,
    attendee_id: int,
    attendee: attendees_schemas.AttendeeUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return application_crud.update_attendee(
        db=db,
        application_id=application_id,
        attendee_id=attendee_id,
        attendee=attendee,
        user=current_user,
    )
