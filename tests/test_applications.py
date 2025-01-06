import pytest
from fastapi import status

from tests.conftest import get_auth_headers_for_citizen


@pytest.fixture
def test_application(test_citizen, test_popup_city):
    return {
        'first_name': 'Test',
        'last_name': 'User',
        'citizen_id': test_citizen.id,
        'popup_city_id': test_popup_city.id,
    }


def test_create_application_success(client, auth_headers, test_application):
    response = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['first_name'] == test_application['first_name']
    assert data['last_name'] == test_application['last_name']
    assert data['citizen_id'] == test_application['citizen_id']
    assert data['popup_city_id'] == test_application['popup_city_id']


def test_create_application_unauthorized(client, test_application):
    response = client.post('/applications/', json=test_application)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_applications_success(client, test_application):
    citizen_id = test_application['citizen_id']
    headers = get_auth_headers_for_citizen(citizen_id)
    # First create an application
    client.post('/applications/', json=test_application, headers=headers)

    response = client.get('/applications/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]['first_name'] == test_application['first_name']
    assert data[0]['last_name'] == test_application['last_name']
    assert data[0]['citizen_id'] == citizen_id


def test_get_application_by_id_success(client, test_application):
    citizen_id = test_application['citizen_id']
    headers = get_auth_headers_for_citizen(citizen_id)
    # First create an application
    create_response = client.post(
        '/applications/',
        json=test_application,
        headers=headers,
    )
    application_id = create_response.json()['id']

    response = client.get(f'/applications/{application_id}', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['id'] == application_id
    assert data['citizen_id'] == citizen_id


def test_update_application_success(client, auth_headers, test_application):
    # First create an application
    create_response = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    application_id = create_response.json()['id']

    update_data = {'first_name': 'Updated'}
    response = client.put(
        f'/applications/{application_id}', json=update_data, headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['first_name'] == 'Updated'


@pytest.mark.asyncio
async def test_create_attendee_success(client, auth_headers, test_application):
    # First create an application
    create_response = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    application_id = create_response.json()['id']

    attendee_data = {
        'name': 'Test Attendee',
        'category': 'spouse',
        'email': 'spouse@example.com',
    }

    response = client.post(
        f'/applications/{application_id}/attendees',
        json=attendee_data,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data['attendees']) > 0
    # main attendee is created by default
    assert data['attendees'][0]['category'] == 'main'
    created_attendee = next(a for a in data['attendees'] if a['category'] == 'spouse')
    assert created_attendee['name'] == attendee_data['name']
    assert created_attendee['category'] == attendee_data['category']
    assert created_attendee['email'] == attendee_data['email']


def test_get_applications_for_different_citizens(
    client, create_test_citizen, test_popup_city
):
    # Create two different citizens
    citizen1 = create_test_citizen(1)
    citizen2 = create_test_citizen(2)

    # Create application data
    application1 = {
        'first_name': 'Test1',
        'last_name': 'User',
        'citizen_id': citizen1.id,
        'popup_city_id': test_popup_city.id,
    }

    # Get auth headers for first citizen
    headers1 = get_auth_headers_for_citizen(citizen1.id)

    # Create application for first citizen
    response = client.post('/applications/', json=application1, headers=headers1)
    assert response.status_code == status.HTTP_201_CREATED

    # First citizen should see their application
    response1 = client.get('/applications/', headers=headers1)
    assert response1.status_code == status.HTTP_200_OK
    data1 = response1.json()
    assert len(data1) == 1
    assert data1[0]['citizen_id'] == citizen1.id

    # Second citizen should see no applications
    headers2 = get_auth_headers_for_citizen(citizen2.id)
    response2 = client.get('/applications/', headers=headers2)
    assert response2.status_code == status.HTTP_200_OK
    data2 = response2.json()
    assert len(data2) == 0


def test_info_not_shared(client, auth_headers, test_application):
    application = test_application.copy()
    application['info_not_shared'] = ['Last name']
    response = client.post('/applications/', json=application, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['first_name'] == test_application['first_name']
    assert data['last_name'] == test_application['last_name']
    assert data['info_not_shared'] == application['info_not_shared']

    application_id = data['id']

    update_data = {'info_not_shared': ['Last name', 'email']}
    response = client.put(
        f'/applications/{application_id}', json=update_data, headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['info_not_shared'] == update_data['info_not_shared']

    response = client.get(f'/applications/{application_id}', headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['info_not_shared'] == update_data['info_not_shared']


def test_create_application_with_invalid_status(client, auth_headers, test_application):
    test_application['status'] = 'accepted'
    response = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test with a valid status
    test_application['status'] = 'draft'
    response = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()['status'] == 'draft'


def test_update_application_with_invalid_status(client, auth_headers, test_application):
    response = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    application_id = response.json()['id']

    test_application['status'] = 'accepted'
    response = client.put(
        f'/applications/{application_id}', json=test_application, headers=auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test with a valid status
    test_application['status'] = 'in review'
    response = client.put(
        f'/applications/{application_id}', json=test_application, headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == 'in review'


def test_application_status_validation(
    client, auth_headers, test_application, db_session
):
    from app.api.applications.models import Application
    from app.api.applications.schemas import ApplicationStatus, TicketCategory

    # First create a basic application
    test_application['status'] = ApplicationStatus.IN_REVIEW.value
    response = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()['status'] == test_application['status']
    assert response.json()['ticket_category'] is None
    assert response.json()['discount_assigned'] is None
    application_id = response.json()['id']

    # Test 1: Can't be ACCEPTED without ticket category
    application = (
        db_session.query(Application).filter(Application.id == application_id).first()
    )
    application.status = ApplicationStatus.ACCEPTED.value
    db_session.commit()

    response = client.get(f'/applications/{application_id}', headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == ApplicationStatus.IN_REVIEW.value
    assert response.json()['ticket_category'] is None
    assert response.json()['discount_assigned'] is None

    # Test 2: Can be ACCEPTED with STANDARD ticket
    application = (
        db_session.query(Application).filter(Application.id == application_id).first()
    )
    application.status = ApplicationStatus.ACCEPTED.value
    application.ticket_category = TicketCategory.STANDARD.value
    db_session.commit()

    response = client.get(f'/applications/{application_id}', headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == ApplicationStatus.ACCEPTED.value
    assert response.json()['ticket_category'] == TicketCategory.STANDARD.value
    assert response.json()['discount_assigned'] is None

    # Test 3: Can't be ACCEPTED with DISCOUNTED ticket without discount assigned
    application = (
        db_session.query(Application).filter(Application.id == application_id).first()
    )
    application.status = ApplicationStatus.ACCEPTED.value
    application.ticket_category = TicketCategory.DISCOUNTED.value
    application.discount_assigned = None
    db_session.commit()

    response = client.get(f'/applications/{application_id}', headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == ApplicationStatus.IN_REVIEW.value
    assert response.json()['ticket_category'] == TicketCategory.DISCOUNTED.value
    assert response.json()['discount_assigned'] is None

    # Test 4: Can be ACCEPTED with DISCOUNTED ticket and discount assigned
    application = (
        db_session.query(Application).filter(Application.id == application_id).first()
    )
    application.status = ApplicationStatus.ACCEPTED.value
    application.ticket_category = TicketCategory.DISCOUNTED.value
    application.discount_assigned = '10'
    db_session.commit()

    response = client.get(f'/applications/{application_id}', headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == ApplicationStatus.ACCEPTED.value
    assert response.json()['ticket_category'] == TicketCategory.DISCOUNTED.value
    assert response.json()['discount_assigned'] == 10
