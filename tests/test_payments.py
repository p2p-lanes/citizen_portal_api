from unittest.mock import patch

import pytest
from fastapi import status

from app.api.applications.schemas import ApplicationStatus, TicketCategory
from app.api.payments.schemas import PaymentSource
from tests.conftest import get_auth_headers_for_citizen


@pytest.fixture
def test_payment_data(test_application, client, auth_headers):
    # First create an application
    response = client.post(
        '/applications/', json=test_application, headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    application = response.json()
    application_id = application['id']

    # Create an attendee
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
    attendee = response.json()['attendees'][1]  # Index 1 is the spouse

    return {
        'application_id': application_id,
        'products': [
            {
                'product_id': 1,
                'attendee_id': attendee['id'],
                'quantity': 1,
            }
        ],
    }


@pytest.fixture
def test_product(db_session):
    from app.api.products.models import Product

    product = Product(
        id=1,
        name='Test Product',
        slug='test-product',
        description='Test Description',
        price=100.0,
        category='ticket',
        popup_city_id=1,
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    return product


def test_create_payment_unauthorized(client, test_payment_data):
    response = client.post('/payments/', json=test_payment_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.fixture
def mock_simplefi_response():
    return {
        'id': 'test_payment_id',
        'status': 'pending',
        'checkout_url': 'https://test.checkout.url',
    }


@pytest.fixture
def mock_create_payment(mock_simplefi_response):
    with patch('app.core.simplefi.create_payment') as mock:
        mock.return_value = mock_simplefi_response
        yield mock


def test_create_payment_success(
    client,
    auth_headers,
    test_payment_data,
    test_product,
    db_session,
    mock_create_payment,
):
    from app.api.applications.models import Application

    application = db_session.get(Application, test_payment_data['application_id'])
    application.status = ApplicationStatus.ACCEPTED.value
    application.ticket_category = TicketCategory.STANDARD.value
    db_session.commit()

    response = client.post('/payments/', json=test_payment_data, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data['application_id'] == test_payment_data['application_id']
    assert data['amount'] > 0
    assert data['currency'] == 'USD'
    assert data['status'] == 'pending'
    assert data['external_id'] is not None
    assert data['checkout_url'] is not None

    # Verify simplefi.create_payment was called with correct arguments
    mock_create_payment.assert_called_once()
    call_args = mock_create_payment.call_args
    assert call_args.args[0] == data['amount']
    assert 'reference' in call_args.kwargs


def test_create_payment_application_not_accepted(
    client, auth_headers, test_payment_data
):
    response = client.post('/payments/', json=test_payment_data, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Application is not accepted'


def test_get_payments(
    client,
    auth_headers,
    test_payment_data,
    test_product,
    mock_create_payment,
    db_session,
):
    # First create a payment
    from app.api.applications.models import Application

    application = db_session.get(Application, test_payment_data['application_id'])
    application.status = ApplicationStatus.ACCEPTED.value
    application.ticket_category = TicketCategory.STANDARD.value
    db_session.commit()

    create_response = client.post(
        '/payments/', json=test_payment_data, headers=auth_headers
    )
    assert create_response.status_code == status.HTTP_200_OK

    # Now get all payments
    response = client.get('/payments/', headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]['application_id'] == test_payment_data['application_id']


def test_get_payment_by_id(
    client,
    auth_headers,
    test_payment_data,
    test_product,
    mock_create_payment,
    db_session,
):
    # First create a payment
    from app.api.applications.models import Application

    application = db_session.get(Application, test_payment_data['application_id'])
    application.status = ApplicationStatus.ACCEPTED.value
    application.ticket_category = TicketCategory.STANDARD.value
    db_session.commit()

    create_response = client.post(
        '/payments/', json=test_payment_data, headers=auth_headers
    )
    payment_id = create_response.json()['id']

    response = client.get(f'/payments/{payment_id}', headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['id'] == payment_id


def test_get_payment_other_citizen(
    client,
    auth_headers,
    test_payment_data,
    test_product,
    mock_create_payment,
    db_session,
):
    # First create a payment
    from app.api.applications.models import Application

    application = db_session.get(Application, test_payment_data['application_id'])
    application.status = ApplicationStatus.ACCEPTED.value
    application.ticket_category = TicketCategory.STANDARD.value
    db_session.commit()

    create_response = client.post(
        '/payments/', json=test_payment_data, headers=auth_headers
    )
    payment_id = create_response.json()['id']

    # Try to get payment with different citizen
    other_headers = get_auth_headers_for_citizen(999)
    response = client.get(f'/payments/{payment_id}', headers=other_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_simplefi_webhook_payment_approval(
    client,
    auth_headers,
    test_payment_data,
    test_product,
    mock_create_payment,
    mock_simplefi_response,
    db_session,
):
    # First create a payment
    from app.api.applications.models import Application

    application = db_session.get(Application, test_payment_data['application_id'])
    application.status = ApplicationStatus.ACCEPTED.value
    application.ticket_category = TicketCategory.STANDARD.value
    db_session.commit()

    create_response = client.post(
        '/payments/', json=test_payment_data, headers=auth_headers
    )
    payment = create_response.json()

    webhook_data = {
        'id': 'test_id',
        'event_type': 'new_payment',
        'entity_type': 'payment_request',
        'entity_id': payment['external_id'],
        'data': {
            'payment_request': {
                'id': mock_simplefi_response['id'],
                'order_id': 1,
                'amount': 100.0,
                'amount_paid': 100.0,
                'currency': 'USD',
                'reference': {},
                'status': 'approved',
                'status_detail': 'correct',
                'transactions': [],
                'card_payment': None,
                'payments': [],
            },
            'new_payment': {
                'coin': 'ETH',
                'hash': 'test_hash',
                'amount': payment['amount'],
                'paid_at': '2024-01-01T00:00:00Z',
            },
        },
    }

    response = client.post('/webhooks/simplefi', json=webhook_data)
    assert response.status_code == status.HTTP_200_OK

    # Verify payment was approved
    payment_response = client.get(f'/payments/{payment["id"]}', headers=auth_headers)
    assert payment_response.json()['status'] == 'approved'
    assert payment_response.json()['source'] == PaymentSource.SIMPLEFI.value


def test_simplefi_webhook_payment_expired(
    client,
    auth_headers,
    test_payment_data,
    test_product,
    mock_create_payment,
    mock_simplefi_response,
    db_session,
):
    # First create a payment
    from app.api.applications.models import Application

    application = db_session.get(Application, test_payment_data['application_id'])
    application.status = ApplicationStatus.ACCEPTED.value
    application.ticket_category = TicketCategory.STANDARD.value
    db_session.commit()

    create_response = client.post(
        '/payments/', json=test_payment_data, headers=auth_headers
    )
    payment = create_response.json()

    webhook_data = {
        'id': 'test_id',
        'event_type': 'new_payment',
        'entity_type': 'payment_request',
        'entity_id': payment['external_id'],
        'data': {
            'payment_request': {
                'id': mock_simplefi_response['id'],
                'order_id': 1,
                'amount': 100.0,
                'amount_paid': 100.0,
                'currency': 'USD',
                'reference': {},
                'status': 'expired',
                'status_detail': 'not_paid',
                'transactions': [],
                'card_payment': None,
                'payments': [],
            },
            'new_payment': {
                'coin': 'USD',
                'hash': 'test_hash',
                'amount': payment['amount'],
                'paid_at': '2024-01-01T00:00:00Z',
            },
        },
    }

    response = client.post('/webhooks/simplefi', json=webhook_data)
    assert response.status_code == status.HTTP_200_OK

    # Verify payment was expired
    payment_response = client.get(f'/payments/{payment["id"]}', headers=auth_headers)
    assert payment_response.json()['status'] == 'expired'


def test_simplefi_webhook_invalid_event_type(client, mock_simplefi_response):
    webhook_data = {
        'id': 'test_id',
        'event_type': 'invalid_event_type',
        'entity_type': 'payment_request',
        'entity_id': '123',
        'data': {
            'payment_request': {
                'id': mock_simplefi_response['id'],
                'order_id': 1,
                'amount': 100.0,
                'amount_paid': 100.0,
                'currency': 'USD',
                'reference': {},
                'status': 'expired',
                'status_detail': 'not_paid',
                'transactions': [],
                'card_payment': None,
                'payments': [],
            },
            'new_payment': {
                'coin': 'USD',
                'hash': 'test_hash',
                'amount': 100.0,
                'paid_at': '2024-01-01T00:00:00Z',
            },
        },
    }

    response = client.post('/webhooks/simplefi', json=webhook_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    err_msg = 'Event type is not new_payment or new_card_payment'
    assert response.json()['detail'] == err_msg
