import pytest
from fastapi import status


def test_signup_success(client):
    response = client.post(
        '/citizens/signup',
        json={
            'primary_email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['primary_email'] == 'test@example.com'
    assert data['id'] is not None


def test_signup_duplicate_email(client):
    # First signup
    client.post(
        '/citizens/signup',
        json={
            'primary_email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
        },
    )

    # Duplicate signup
    response = client.post(
        '/citizens/signup',
        json={
            'primary_email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
        },
    )
    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_authenticate_success(client):
    response = client.post('/citizens/authenticate', json={'email': 'test@example.com'})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['message'] == 'Mail sent successfully'


def test_login_success(client, db_session):
    # First create a citizen with known spice
    from app.api.citizens.crud import citizen
    from app.api.citizens.schemas import InternalCitizenCreate

    test_spice = 'testspice123'
    new_citizen = InternalCitizenCreate(
        primary_email='test@example.com', spice=test_spice
    )
    citizen.create(db_session, new_citizen)

    response = client.post(
        '/citizens/login', params={'email': 'test@example.com', 'spice': test_spice}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['access_token'] is not None
    assert data['token_type'] == 'Bearer'
