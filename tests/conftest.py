import asyncio
from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.citizens.models import Citizen
from app.api.coupon_codes.models import CouponCode
from app.api.popup_city.models import PopUpCity
from app.api.webhooks.dependencies import get_webhook_cache
from app.core.config import Environment, settings
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.core.utils import current_time
from main import app


@pytest.fixture(scope='session', autouse=True)
def check_test_environment():
    if settings.ENVIRONMENT != Environment.TEST:
        raise RuntimeError(
            f'Tests can only be executed in test environment. Current environment: {settings.ENVIRONMENT}'
        )


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def test_db_engine():
    engine = create_engine(
        settings.SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope='function')
def db_session(test_db_engine):
    """Create a fresh database session for each test"""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )

    # Drop and recreate all tables before each test
    Base.metadata.drop_all(bind=test_db_engine)
    Base.metadata.create_all(bind=test_db_engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Optionally, drop all tables after each test
        # Base.metadata.drop_all(bind=test_db_engine)


@pytest.fixture(scope='function')
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def get_auth_headers_for_citizen(citizen_id: int) -> dict:
    """Generate auth headers for a specific citizen ID"""
    user_data = {
        'citizen_id': citizen_id,
        'email': f'test{citizen_id}@example.com',
    }
    access_token = create_access_token(data=user_data)
    return {'Authorization': f'Bearer {access_token}'}


@pytest.fixture(scope='function')
def create_test_citizen(db_session):
    """Factory fixture to create test citizens"""

    def _create_citizen(citizen_id: int):
        citizen = Citizen(
            # id=citizen_id,
            primary_email=f'test{citizen_id}@example.com',
            first_name=f'Test{citizen_id}',
            last_name='User',
            email_validated=True,
        )
        db_session.add(citizen)
        db_session.commit()
        return citizen

    yield _create_citizen


@pytest.fixture(scope='function')
def test_citizen(create_test_citizen):
    """Creates a default test citizen with ID 1"""
    return create_test_citizen(1)


@pytest.fixture(scope='function')
def auth_headers(test_citizen):
    """Creates auth headers for the default test citizen"""
    return get_auth_headers_for_citizen(test_citizen.id)


@pytest.fixture(scope='function')
def test_popup_city(db_session):
    popup = PopUpCity(
        id=1,
        name='Test City',
        slug='test-city',
        location='Test Location',
        visible_in_portal=True,
        clickable_in_portal=True,
        requires_approval=True,
        simplefi_api_key='test_api_key',
    )
    db_session.add(popup)
    db_session.commit()
    return popup


@pytest.fixture
def test_application(test_citizen, test_popup_city):
    """Creates a test application data dictionary"""
    return {
        'first_name': 'Test',
        'last_name': 'User',
        'citizen_id': test_citizen.id,
        'popup_city_id': test_popup_city.id,
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


@pytest.fixture
def test_coupon_code(db_session, test_popup_city):
    coupon_code = CouponCode(
        code='TEST10',
        popup_city_id=test_popup_city.id,
        discount_value=10.0,
        max_uses=100,
        current_uses=0,
        is_active=True,
        start_date=current_time() - timedelta(days=1),
        end_date=current_time() + timedelta(days=1),
    )
    db_session.add(coupon_code)
    db_session.commit()
    return coupon_code


@pytest.fixture
def mock_webhook_cache():
    mock_cache = Mock()
    mock_cache.add.return_value = True  # Always treat webhooks as new
    app.dependency_overrides[get_webhook_cache] = lambda: mock_cache
    yield mock_cache
    app.dependency_overrides.clear()


@pytest.fixture
def mock_email_template(monkeypatch):
    """Mock the get_email_template function to avoid template lookup errors"""
    from app.api.popup_city.crud import popup_city as popup_city_crud

    def mock_get_template(template, *args, **kwargs):
        return template

    monkeypatch.setattr(popup_city_crud, 'get_email_template', mock_get_template)
    return mock_get_template


@pytest.fixture
def mock_create_payment(mock_simplefi_response):
    with patch('app.core.simplefi.create_payment') as mock:
        mock.return_value = mock_simplefi_response
        yield mock


@pytest.fixture
def mock_simplefi_response():
    return {
        'id': 'test_payment_id',
        'status': 'pending',
        'checkout_url': 'https://test.checkout.url',
    }
