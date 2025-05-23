from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.applications import schemas
from app.api.applications.crud import application as application_crud
from app.api.attendees import schemas as attendees_schemas
from app.api.common.schemas import PaginatedResponse, PaginationMetadata
from app.core.database import get_db
from app.core.logger import logger
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
    logger.info('Creating application: %s', application)
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


@router.get(
    '/attendees_directory/{popup_city_id}',
    response_model=PaginatedResponse[schemas.AttendeesDirectory],
)
def get_attendees_directory(
    popup_city_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    attendees, total = application_crud.get_attendees_directory(
        db=db,
        popup_city_id=popup_city_id,
        skip=skip,
        limit=limit,
        user=current_user,
    )
    return PaginatedResponse(
        items=attendees,
        pagination=PaginationMetadata(
            skip=skip,
            limit=limit,
            total=total,
        ),
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
    logger.info('Updating application: %s: %s', application_id, application)
    return application_crud.update(
        db=db,
        id=application_id,
        obj=application,
        user=current_user,
    )


@router.post('/{application_id}/attendees', response_model=schemas.Application)
def create_attendee(
    application_id: int,
    attendee: attendees_schemas.AttendeeCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info('Creating attendee: %s', attendee)
    return application_crud.create_attendee(
        db=db,
        application_id=application_id,
        attendee=attendee,
        user=current_user,
    )


@router.put(
    '/{application_id}/attendees/{attendee_id}',
    response_model=schemas.Application,
)
def update_attendee(
    application_id: int,
    attendee_id: int,
    attendee: attendees_schemas.AttendeeUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info('Updating attendee: %s: %s', attendee_id, attendee)
    return application_crud.update_attendee(
        db=db,
        application_id=application_id,
        attendee_id=attendee_id,
        attendee=attendee,
        user=current_user,
    )


@router.delete(
    '/{application_id}/attendees/{attendee_id}',
    response_model=schemas.Application,
)
def delete_attendee(
    application_id: int,
    attendee_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info('Deleting attendee: %s: %s', application_id, attendee_id)
    return application_crud.delete_attendee(
        db=db,
        application_id=application_id,
        attendee_id=attendee_id,
        user=current_user,
    )
