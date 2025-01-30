from datetime import timedelta

import pytest
from fastapi import status

from app.core.utils import current_time


def test_get_valid_discount_code(client, auth_headers, test_discount_code):
    params = {
        'code': test_discount_code.code,
        'popup_city_id': test_discount_code.popup_city_id,
    }
    response = client.get(
        '/discount-codes',
        params=params,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['code'] == test_discount_code.code
    assert data['discount_type'] == test_discount_code.discount_type
    assert data['discount_value'] == test_discount_code.discount_value


def test_get_inactive_discount_code(
    client, auth_headers, test_discount_code, db_session
):
    test_discount_code.is_active = False
    db_session.commit()

    params = {
        'code': test_discount_code.code,
        'popup_city_id': test_discount_code.popup_city_id,
    }
    response = client.get(
        '/discount-codes',
        params=params,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()['detail'] == 'Discount code is not active'


def test_get_nonexistent_discount_code(client, auth_headers, test_popup_city):
    params = {
        'code': 'INVALID',
        'popup_city_id': test_popup_city.id,
    }
    response = client.get(
        '/discount-codes',
        params=params,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()['detail'] == 'Discount code not found'


def test_get_not_started_discount_code(
    client, auth_headers, test_discount_code, db_session
):
    test_discount_code.start_date = current_time() + timedelta(days=1)
    db_session.commit()

    params = {
        'code': test_discount_code.code,
        'popup_city_id': test_discount_code.popup_city_id,
    }
    response = client.get(
        '/discount-codes',
        params=params,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()['detail'] == 'Discount code has not started yet'


def test_get_expired_discount_code(
    client, auth_headers, test_discount_code, db_session
):
    test_discount_code.end_date = current_time() - timedelta(days=1)
    db_session.commit()

    params = {
        'code': test_discount_code.code,
        'popup_city_id': test_discount_code.popup_city_id,
    }
    response = client.get(
        '/discount-codes',
        params=params,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()['detail'] == 'Discount code has expired'


def test_get_max_uses_reached_discount_code(
    client, auth_headers, test_discount_code, db_session
):
    test_discount_code.max_uses = 5
    test_discount_code.current_uses = 5
    db_session.commit()

    params = {
        'code': test_discount_code.code,
        'popup_city_id': test_discount_code.popup_city_id,
    }
    response = client.get(
        '/discount-codes',
        params=params,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert (
        response.json()['detail']
        == 'Discount code has reached the maximum number of uses'
    )


def test_get_discount_code_unauthorized(client, test_discount_code):
    params = {
        'code': test_discount_code.code,
        'popup_city_id': test_discount_code.popup_city_id,
    }
    response = client.get(
        '/discount-codes',
        params=params,
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.fixture
def test_product(db_session, test_popup_city):
    from app.api.products.models import Product

    product = Product(
        name='Test Product',
        slug='test-product',
        description='Test Description',
        price=100.0,
        category='ticket',
        popup_city_id=test_popup_city.id,
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    return product


def test_payment_with_discount_code(
    client,
    auth_headers,
    test_application,
    test_product,
    test_discount_code,
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

    # Create payment with discount code
    payment_data = {
        'application_id': application_id,
        'products': [
            {'product_id': test_product.id, 'attendee_id': attendee.id, 'quantity': 1}
        ],
        'discount_code': test_discount_code.code,
    }

    response = client.post('/payments', json=payment_data, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Verify the discounted amount (10% off of 100.0)
    assert data['amount'] == 90.0
