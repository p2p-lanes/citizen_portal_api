import pytest
from fastapi import status

from app.api.groups.models import Group, GroupLeader
from tests.conftest import get_auth_headers_for_citizen


@pytest.fixture
def test_group(db_session, test_popup_city, test_citizen):
    """Create a test group with the test citizen as leader"""
    group = Group(
        name='Test Group',
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
