import pytest
from fastapi import status

from app.api.applications.models import ApplicationStatus
from app.api.citizens.models import Citizen
from app.api.groups.models import Group, GroupLeader
from app.core.config import settings
from tests.conftest import get_auth_headers_for_citizen


@pytest.fixture
def test_group(db_session, test_popup_city, test_citizen):
    """Create a test group with the test citizen as leader"""
    group = Group(
        name='Test Group',
        slug='test-group',
        description='Test Description',
        discount_percentage=10.0,
        popup_city_id=test_popup_city.id,
        max_members=5,
    )
    db_session.add(group)
    db_session.flush()

    group_leader = GroupLeader(citizen_id=test_citizen.id, group_id=group.id)
    db_session.add(group_leader)
    db_session.commit()
    return group


def test_get_groups_success(client, auth_headers, test_group):
    """Test getting all groups where user is leader"""
    response = client.get('/groups', headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]['name'] == test_group.name
    assert data[0]['description'] == test_group.description
    assert data[0]['discount_percentage'] == test_group.discount_percentage
    assert data[0]['popup_city_id'] == test_group.popup_city_id
    assert data[0]['max_members'] == test_group.max_members


def test_get_groups_unauthorized(client):
    """Test getting groups without authentication"""
    response = client.get('/groups')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_groups_empty_for_non_leader(client, create_test_citizen, test_group):
    """Test that non-leaders don't see any groups"""
    non_leader = create_test_citizen(2)
    headers = get_auth_headers_for_citizen(non_leader.id)

    response = client.get('/groups', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0


def test_get_group_by_id_success(client, auth_headers, test_group):
    """Test getting a specific group by ID"""
    response = client.get(f'/groups/{test_group.id}', headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['id'] == test_group.id
    assert data['name'] == test_group.name


def test_get_group_by_slug_success(client, test_group):
    """Test getting a specific group by slug"""
    headers = {'api-key': settings.GROUPS_API_KEY}
    response = client.get(f'/groups/aux/{test_group.slug}', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['id'] == test_group.id
    assert data['name'] == test_group.name
    assert data['popup_name'] == test_group.popup_city.name


def test_get_group_by_id_not_found(client, auth_headers):
    """Test getting a non-existent group"""
    response = client.get('/groups/999', headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_group_by_id_unauthorized(client, test_group):
    """Test getting a group without authentication"""
    response = client.get(f'/groups/{test_group.id}')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_group_by_id_forbidden(client, create_test_citizen, test_group):
    """Test that non-leaders can't access the group"""
    non_leader = create_test_citizen(2)
    headers = get_auth_headers_for_citizen(non_leader.id)

    response = client.get(f'/groups/{test_group.id}', headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_groups_with_filters(client, auth_headers, test_group):
    """Test getting groups with filters"""
    # Test filter by name
    response = client.get(
        '/groups', params={'name': test_group.name}, headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]['id'] == test_group.id

    # Test filter by popup_city_id
    response = client.get(
        '/groups',
        params={'popup_city_id': test_group.popup_city_id},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]['id'] == test_group.id

    # Test filter with no matches
    response = client.get(
        '/groups', params={'name': 'Non-existent Group'}, headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0


def test_get_groups_with_sorting(client, auth_headers, test_group, db_session):
    """Test getting groups with different sorting options"""
    # Create a second group
    group2 = Group(
        name='Another Group',
        slug='another-group',
        description='Another Description',
        discount_percentage=15.0,
        popup_city_id=test_group.popup_city_id,
        max_members=10,
    )
    db_session.add(group2)
    db_session.flush()

    group_leader = GroupLeader(citizen_id=test_group.leaders[0].id, group_id=group2.id)
    db_session.add(group_leader)
    db_session.commit()

    # Test sorting by name ascending
    response = client.get(
        '/groups',
        params={'sort_by': 'name', 'sort_order': 'asc'},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]['name'] == 'Another Group'
    assert data[1]['name'] == 'Test Group'

    # Test sorting by name descending
    response = client.get(
        '/groups',
        params={'sort_by': 'name', 'sort_order': 'desc'},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]['name'] == 'Test Group'
    assert data[1]['name'] == 'Another Group'


def test_get_groups_invalid_sort_field(client, auth_headers):
    """Test getting groups with invalid sort field"""
    response = client.get(
        '/groups', params={'sort_by': 'invalid_field'}, headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'Invalid sort field' in response.json()['detail']


@pytest.mark.parametrize('identifier_type', ['id', 'slug'])
def test_add_new_member_success(
    client, db_session, auth_headers, test_group, identifier_type
):
    """Test successfully adding a new member to a group using either ID or slug"""
    # validate that the citizen does not exist
    email = 'john.doe@example.com'
    citizen = db_session.query(Citizen).filter(Citizen.primary_email == email).first()
    assert citizen is None

    member_data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': email,
    }

    # Use either ID or slug based on the parameter
    group_identifier = test_group.id if identifier_type == 'id' else test_group.slug
    response = client.post(
        f'/groups/{group_identifier}/new_member',
        json=member_data,
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    application_id = data['id']
    assert data['group_id'] == test_group.id
    assert data['email'] == email
    assert data['first_name'] == member_data['first_name']
    assert data['last_name'] == member_data['last_name']
    assert data['authorization']['token_type'] == 'Bearer'
    assert data['authorization']['access_token'] is not None

    citizen = db_session.query(Citizen).filter(Citizen.primary_email == email).first()
    assert citizen is not None
    assert citizen.first_name == member_data['first_name']
    assert citizen.last_name == member_data['last_name']
    assert citizen.primary_email == member_data['email']

    applications = citizen.applications
    assert len(applications) == 1
    application = applications[0]
    assert application.id == application_id
    assert application.group_id == test_group.id
    assert application.status == ApplicationStatus.ACCEPTED
    assert application.first_name == member_data['first_name']
    assert application.last_name == member_data['last_name']
    assert application.email == member_data['email']


def test_add_new_member_unauthorized(client, test_group):
    """Test adding a member without token fails"""
    member_data = {
        'first_name': 'New',
        'last_name': 'Member',
        'email': 'new.member@example.com',
    }

    response = client.post(f'/groups/{test_group.id}/new_member', json=member_data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == 'Not authenticated'


def test_add_new_member_invalid_token(client, test_group):
    """Test adding a member with invalid API key fails"""
    member_data = {
        'first_name': 'New',
        'last_name': 'Member',
        'email': 'new.member@example.com',
    }

    response = client.post(
        f'/groups/{test_group.id}/new_member',
        json=member_data,
        headers={'Authorization': 'Bearer invalid_key'},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == 'Could not validate credentials'


def test_add_new_member_invalid_data(client, test_group, auth_headers):
    """Test adding a member with invalid data fails"""
    invalid_member_data = {
        'first_name': '',  # Empty first name should fail validation
        'last_name': 'Member',
        'email': 'invalid-email',  # Invalid email should fail validation
    }

    response = client.post(
        f'/groups/{test_group.id}/new_member',
        json=invalid_member_data,
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_add_new_member_nonexistent_group(client, auth_headers):
    """Test adding a member to a non-existent group fails"""
    member_data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com',
    }

    response = client.post(
        '/groups/99999/new_member',  # Non-existent group ID
        json=member_data,
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()['detail'] == 'Group not found'

    response = client.post(
        '/groups/non-existent-slug/new_member',  # Non-existent group slug
        json=member_data,
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()['detail'] == 'Group not found'
