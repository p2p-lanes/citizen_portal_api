from fastapi import status


def test_invalid_token(client):
    response = client.get(
        '/applications/', headers={'Authorization': 'Bearer invalid_token'}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_expired_token(client):
    from datetime import datetime, timedelta

    from jose import jwt

    from app.core.config import settings

    expired_token = jwt.encode(
        {
            'citizen_id': 1,
            'email': 'test@example.com',
            'exp': datetime.utcnow() - timedelta(minutes=1),
        },
        settings.SECRET_KEY,
        algorithm='HS256',
    )

    response = client.get(
        '/applications/', headers={'Authorization': f'Bearer {expired_token}'}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == 'Token has expired'
