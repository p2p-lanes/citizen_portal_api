from datetime import timedelta

from fastapi import status

from app.core.utils import current_time


def test_get_valid_coupon_code(client, auth_headers, test_coupon_code):
    params = {
        'code': test_coupon_code.code,
        'popup_city_id': test_coupon_code.popup_city_id,
    }
    response = client.get(
        '/coupon-codes',
        params=params,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['code'] == test_coupon_code.code
    assert data['discount_value'] == test_coupon_code.discount_value


def test_get_inactive_coupon_code(client, auth_headers, test_coupon_code, db_session):
    test_coupon_code.is_active = False
    db_session.commit()

    params = {
        'code': test_coupon_code.code,
        'popup_city_id': test_coupon_code.popup_city_id,
    }
    response = client.get(
        '/coupon-codes',
        params=params,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()['detail'] == 'Coupon code is not active'


def test_get_nonexistent_coupon_code(client, auth_headers, test_popup_city):
    params = {
        'code': 'INVALID',
        'popup_city_id': test_popup_city.id,
    }
    response = client.get(
        '/coupon-codes',
        params=params,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert (
        response.json()['detail']
        == 'Coupon code not found. Please, enter a valid coupon.'
    )


def test_get_not_started_coupon_code(
    client, auth_headers, test_coupon_code, db_session
):
    test_coupon_code.start_date = current_time() + timedelta(days=1)
    db_session.commit()

    params = {
        'code': test_coupon_code.code,
        'popup_city_id': test_coupon_code.popup_city_id,
    }
    response = client.get(
        '/coupon-codes',
        params=params,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()['detail'] == 'Coupon code has not started yet'


def test_get_expired_coupon_code(client, auth_headers, test_coupon_code, db_session):
    test_coupon_code.end_date = current_time() - timedelta(days=1)
    db_session.commit()

    params = {
        'code': test_coupon_code.code,
        'popup_city_id': test_coupon_code.popup_city_id,
    }
    response = client.get(
        '/coupon-codes',
        params=params,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()['detail'] == 'Coupon code has expired'


def test_get_max_uses_reached_coupon_code(
    client, auth_headers, test_coupon_code, db_session
):
    test_coupon_code.max_uses = 5
    test_coupon_code.current_uses = 5
    db_session.commit()

    params = {
        'code': test_coupon_code.code,
        'popup_city_id': test_coupon_code.popup_city_id,
    }
    response = client.get(
        '/coupon-codes',
        params=params,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert (
        response.json()['detail']
        == 'Coupon code has reached the maximum number of uses'
    )


def test_get_coupon_code_unauthorized(client, test_coupon_code):
    params = {
        'code': test_coupon_code.code,
        'popup_city_id': test_coupon_code.popup_city_id,
    }
    response = client.get(
        '/coupon-codes',
        params=params,
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_payment_with_coupon_code(
    client,
    auth_headers,
    test_application,
    test_products,
    test_coupon_code,
    mock_create_payment,
    db_session,
):
    from app.api.applications.attendees.models import Attendee
    from app.api.applications.models import Application
    from app.api.applications.schemas import ApplicationStatus

    # Create application and set it to accepted
    response = client.post('/applications', json=test_application, headers=auth_headers)
    application_id = response.json()['id']
    application = db_session.get(Application, application_id)
    application.status = ApplicationStatus.ACCEPTED.value
    db_session.commit()

    # Get the main attendee
    attendee = (
        db_session.query(Attendee)
        .filter(Attendee.application_id == application_id, Attendee.category == 'main')
        .first()
    )

    # Create payment with coupon code
    test_product = test_products[0]
    payment_data = {
        'application_id': application_id,
        'products': [
            {
                'product_id': test_product.id,
                'attendee_id': attendee.id,
                'quantity': 1,
            }
        ],
        'coupon_code': test_coupon_code.code,
    }

    response = client.post('/payments', json=payment_data, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Verify the discounted amount (10% off of 100.0)
    assert data['amount'] == 90.0
