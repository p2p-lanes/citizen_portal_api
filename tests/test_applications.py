from fastapi import status

from app.api.applications.schemas import ApplicationStatus
from tests.conftest import get_auth_headers_for_citizen


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


def test_create_application_auto_approves_when_approval_not_required(
    client, auth_headers, test_application, db_session
):
    from app.api.popup_city.models import PopUpCity

    popup_city = db_session.get(PopUpCity, test_application['popup_city_id'])
    popup_city.requires_approval = False
    db_session.commit()

    test_application['status'] = ApplicationStatus.IN_REVIEW.value
    response = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['status'] == ApplicationStatus.ACCEPTED.value
    assert data['discount_assigned'] is None


def test_update_application_auto_approves_when_approval_not_required(
    client, auth_headers, test_application, db_session
):
    from app.api.popup_city.models import PopUpCity

    popup_city = db_session.get(PopUpCity, test_application['popup_city_id'])
    popup_city.requires_approval = False
    db_session.commit()

    test_application['status'] = ApplicationStatus.DRAFT.value
    response = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['status'] == ApplicationStatus.DRAFT.value
    application_id = data['id']

    to_update = {'status': ApplicationStatus.IN_REVIEW.value}
    response = client.put(
        f'/applications/{application_id}', json=to_update, headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['status'] == ApplicationStatus.ACCEPTED.value
    assert data['discount_assigned'] is None


def test_create_application_duplicate_popup_city(
    client, auth_headers, test_application
):
    response = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    assert response.status_code == status.HTTP_409_CONFLICT


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


def test_get_application_from_other_citizen(client, test_application):
    citizen_id = test_application['citizen_id']
    create_response = client.post(
        '/applications/',
        json=test_application,
        headers=get_auth_headers_for_citizen(citizen_id),
    )
    application_id = create_response.json()['id']

    response = client.get(
        f'/applications/{application_id}',
        headers=get_auth_headers_for_citizen(citizen_id + 1),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_application_for_other_citizen(client, test_application):
    citizen_id = test_application['citizen_id']
    response = client.post(
        '/applications/',
        json=test_application,
        headers=get_auth_headers_for_citizen(citizen_id + 1),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


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


def test_create_attendee_success(client, auth_headers, test_application):
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


def test_create_existing_attendee_spouse(client, auth_headers, test_application):
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

    attendee_data = {
        'name': 'Test Attendee',
        'category': 'spouse',
        'email': 'spouse2@example.com',
    }
    response = client.post(
        f'/applications/{application_id}/attendees',
        json=attendee_data,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Attendee spouse already exists'


def test_create_existing_attendee_by_email(client, auth_headers, test_application):
    create_response = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    application_id = create_response.json()['id']

    attendee_data = {
        'name': 'Test Attendee',
        'category': 'kid',
        'email': 'kid@example.com',
    }
    response = client.post(
        f'/applications/{application_id}/attendees',
        json=attendee_data,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK

    response = client.post(
        f'/applications/{application_id}/attendees',
        json=attendee_data,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    err_msg = f'Attendee {attendee_data["email"]} already exists'
    assert response.json()['detail'] == err_msg


def test_update_attendee_success(client, auth_headers, test_application):
    create_response = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    application_id = create_response.json()['id']

    attendee_data = {
        'name': 'Test Attendee',
        'category': 'kid',
        'email': 'kid@test.com',
    }
    response = client.post(
        f'/applications/{application_id}/attendees',
        json=attendee_data,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK

    attendee_id = response.json()['attendees'][1]['id']
    update_data = {
        'name': 'Updated Attendee',
        'email': attendee_data['email'],
        'category': 'spouse',  # Can't change category
    }
    response = client.put(
        f'/applications/{application_id}/attendees/{attendee_id}',
        json=update_data,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    updated_attendee = next(a for a in data['attendees'] if a['id'] == attendee_id)
    assert updated_attendee['name'] == update_data['name']
    assert updated_attendee['category'] == attendee_data['category']  # unchanged
    assert updated_attendee['email'] == update_data['email']


def test_update_attendee_existing_email(client, auth_headers, test_application):
    create_response = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    application_id = create_response.json()['id']

    email1 = 'kid@test.com'
    attendee_data = {
        'name': 'Test Attendee',
        'category': 'kid',
        'email': email1,
    }
    response = client.post(
        f'/applications/{application_id}/attendees',
        json=attendee_data,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK

    attendee_data['email'] = 'kid2@test.com'
    response = client.post(
        f'/applications/{application_id}/attendees',
        json=attendee_data,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    attendees = response.json()['attendees']
    kid2_id = next(a['id'] for a in attendees if a['email'] == attendee_data['email'])

    response = client.put(
        f'/applications/{application_id}/attendees/{kid2_id}',
        json={'email': email1},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    err_msg = f'Attendee {email1} already exists'
    assert response.json()['detail'] == err_msg


def test_delete_attendee_success(client, auth_headers, test_application):
    create_response = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    application_id = create_response.json()['id']

    attendee_data = {
        'name': 'Test Attendee',
        'category': 'kid',
        'email': 'kid@test.com',
    }
    response = client.post(
        f'/applications/{application_id}/attendees',
        json=attendee_data,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    attendee_id = response.json()['attendees'][1]['id']

    response = client.delete(
        f'/applications/{application_id}/attendees/{attendee_id}',
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK


def test_delete_main_attendee(client, auth_headers, test_application):
    create_response = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    application_id = create_response.json()['id']
    attendee_id = create_response.json()['attendees'][0]['id']

    response = client.delete(
        f'/applications/{application_id}/attendees/{attendee_id}',
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Cannot delete main attendee'


def test_delete_attendee_not_found(client, auth_headers, test_application):
    create_response = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    application_id = create_response.json()['id']

    response = client.delete(
        f'/applications/{application_id}/attendees/999',
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Attendee not found'


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

    # First create a basic application
    test_application['status'] = ApplicationStatus.IN_REVIEW.value
    test_application['scholarship_request'] = True
    response = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()['status'] == test_application['status']
    assert response.json()['discount_assigned'] is None
    assert response.json()['scholarship_request'] is True
    application_id = response.json()['id']

    # Test 1: Can't be ACCEPTED without discount assigned if scholarship request is True
    application = (
        db_session.query(Application).filter(Application.id == application_id).first()
    )
    application.status = ApplicationStatus.ACCEPTED.value
    db_session.commit()

    response = client.get(f'/applications/{application_id}', headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == ApplicationStatus.IN_REVIEW.value
    assert response.json()['discount_assigned'] is None
    assert response.json()['scholarship_request'] is True

    # Test 2: Can be ACCEPTED with discount assigned
    application = (
        db_session.query(Application).filter(Application.id == application_id).first()
    )
    application.status = ApplicationStatus.ACCEPTED.value
    application.discount_assigned = '10'
    db_session.commit()

    response = client.get(f'/applications/{application_id}', headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == ApplicationStatus.ACCEPTED.value
    assert response.json()['discount_assigned'] == 10

    # Test 3: Can be ACCEPTED without discount assigned if scholarship request is False
    application = (
        db_session.query(Application).filter(Application.id == application_id).first()
    )
    application.status = ApplicationStatus.ACCEPTED.value
    application.discount_assigned = None
    application.scholarship_request = False
    db_session.commit()

    response = client.get(f'/applications/{application_id}', headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == ApplicationStatus.ACCEPTED.value
    assert response.json()['discount_assigned'] is None
    assert response.json()['scholarship_request'] is False
