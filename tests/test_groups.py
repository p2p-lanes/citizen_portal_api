import pytest
from fastapi import status

from app.api.applications.models import ApplicationStatus
from app.api.citizens.models import Citizen
from app.api.groups.models import Group, GroupLeader
from app.core.config import settings
from tests.conftest import get_auth_headers_for_citizen


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


def test_get_group_by_id_success(client, auth_headers, test_group, db_session):
    """Test getting a specific group by ID"""
    response = client.get(f'/groups/{test_group.id}', headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['id'] == test_group.id
    assert data['name'] == test_group.name
    assert len(data['members']) == 0

    # add a member to the group
    new_member_data = {
        'email': 'john.doe@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
    }
    response = client.post(
        f'/groups/{test_group.id}/new_member',
        json=new_member_data,
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK

    response = client.get(f'/groups/{test_group.id}', headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['id'] == test_group.id
    assert len(data['members']) == 1
    assert data['name'] == test_group.name
    assert 'products' in data['members'][0]
    assert data['members'][0]['email'] == new_member_data['email']

    citizen_id = data['members'][0]['id']
    citizen = db_session.query(Citizen).filter(Citizen.id == citizen_id).first()
    assert citizen is not None
    assert citizen.primary_email == new_member_data['email']
    assert citizen.first_name == new_member_data['first_name']
    assert citizen.last_name == new_member_data['last_name']
    assert citizen.applications[0].status == ApplicationStatus.ACCEPTED
    assert citizen.applications[0].group_id == test_group.id


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


def test_create_member_success(client, db_session, auth_headers, test_group):
    """Test successfully creating a new member in a group"""
    # Verify the user is actually a leader of the group
    leader = (
        db_session.query(GroupLeader)
        .filter(
            GroupLeader.group_id == test_group.id,
            GroupLeader.citizen_id == test_group.leaders[0].id,
        )
        .first()
    )
    assert leader is not None, 'Test user should be a leader of the group'
    leader_headers = get_auth_headers_for_citizen(leader.citizen_id)

    member_data = {
        'first_name': 'Jane',
        'last_name': 'Smith',
        'email': 'jane.smith@example.com',
    }

    response = client.post(
        f'/groups/{test_group.id}/members',
        json=member_data,
        headers=leader_headers,
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['email'] == member_data['email']
    assert data['first_name'] == member_data['first_name']
    assert data['last_name'] == member_data['last_name']

    group = db_session.query(Group).filter(Group.id == test_group.id).first()
    assert group is not None
    assert len(group.members) == 1
    assert group.members[0].id == data['id']


def test_create_member_as_regular_member(client, db_session, test_group):
    """Test that a regular member (non-leader) can't create new members"""
    # First create a regular member
    member_data = {
        'first_name': 'Regular',
        'last_name': 'Member',
        'email': 'regular.member@example.com',
    }

    # Add member using the leader's auth
    leader_headers = get_auth_headers_for_citizen(test_group.leaders[0].id)
    create_response = client.post(
        f'/groups/{test_group.id}/members',
        json=member_data,
        headers=leader_headers,
    )
    created_member = create_response.json()
    member_id = created_member['id']

    # Verify the member exists but is not a leader
    member_headers = get_auth_headers_for_citizen(member_id)
    leader = (
        db_session.query(GroupLeader)
        .filter(
            GroupLeader.group_id == test_group.id,
            GroupLeader.citizen_id == member_id,
        )
        .first()
    )
    assert leader is None, 'Regular member should not be a leader'

    # Try to create another member as a regular member
    new_member_data = {
        'first_name': 'Another',
        'last_name': 'Member',
        'email': 'another.member@example.com',
    }

    response = client.post(
        f'/groups/{test_group.id}/members',
        json=new_member_data,
        headers=member_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_member_unauthorized(client, test_group):
    """Test creating a member without authentication"""
    member_data = {
        'first_name': 'Jane',
        'last_name': 'Smith',
        'email': 'jane.smith@example.com',
    }

    response = client.post(
        f'/groups/{test_group.id}/members',
        json=member_data,
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_member_forbidden(client, create_test_citizen, test_group):
    """Test that non-leaders can't create members"""
    non_leader = create_test_citizen(2)
    headers = get_auth_headers_for_citizen(non_leader.id)

    member_data = {
        'first_name': 'Jane',
        'last_name': 'Smith',
        'email': 'jane.smith@example.com',
    }

    response = client.post(
        f'/groups/{test_group.id}/members',
        json=member_data,
        headers=headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_member_success(client, db_session, auth_headers, test_group):
    """Test successfully updating a member in a group"""
    # Verify the user is actually a leader of the group
    leader = (
        db_session.query(GroupLeader)
        .filter(
            GroupLeader.group_id == test_group.id,
            GroupLeader.citizen_id == test_group.leaders[0].id,
        )
        .first()
    )
    assert leader is not None, 'Test user should be a leader of the group'
    leader_headers = get_auth_headers_for_citizen(leader.citizen_id)

    # First create a member
    member_data = {
        'first_name': 'Jane',
        'last_name': 'Smith',
        'email': 'jane.smith@example.com',
    }

    create_response = client.post(
        f'/groups/{test_group.id}/members',
        json=member_data,
        headers=leader_headers,
    )
    created_member = create_response.json()
    citizen_id = created_member['id']

    # Now update the member
    updated_data = {
        'first_name': 'Jane Updated',
        'last_name': 'Smith Updated',
        'email': 'jane.updated@example.com',
    }

    response = client.put(
        f'/groups/{test_group.id}/members/{citizen_id}',
        json=updated_data,
        headers=leader_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['email'] == updated_data['email']
    assert data['first_name'] == updated_data['first_name']
    assert data['last_name'] == updated_data['last_name']

    group = db_session.query(Group).filter(Group.id == test_group.id).first()
    assert group is not None
    assert len(group.members) == 1
    assert group.members[0].id == citizen_id


def test_update_member_unauthorized(client, test_group):
    """Test updating a member without authentication"""
    response = client.put(
        f'/groups/{test_group.id}/members/1',
        json={'first_name': 'Test'},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_member_forbidden(client, create_test_citizen, test_group):
    """Test that non-leaders can't update members"""
    non_leader = create_test_citizen(2)
    headers = get_auth_headers_for_citizen(non_leader.id)

    member_data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'test.user@example.com',
        'role': 'member',
        'organization': 'Test Org',
        'gender': 'other',
        'telegram': '@testuser',
    }

    response = client.put(
        f'/groups/{test_group.id}/members/1',
        json=member_data,
        headers=headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_member_as_regular_member(client, db_session, test_group):
    """Test that a regular member (non-leader) can't update other members"""
    # First create two regular members using the leader's auth
    leader_headers = get_auth_headers_for_citizen(test_group.leaders[0].id)

    # Create first member
    member1_data = {
        'first_name': 'Regular',
        'last_name': 'Member',
        'email': 'regular.member@example.com',
    }
    create_response = client.post(
        f'/groups/{test_group.id}/members',
        json=member1_data,
        headers=leader_headers,
    )
    member1 = create_response.json()

    # Create second member
    member2_data = {
        'first_name': 'Another',
        'last_name': 'Member',
        'email': 'another.member@example.com',
    }
    create_response = client.post(
        f'/groups/{test_group.id}/members',
        json=member2_data,
        headers=leader_headers,
    )
    member2 = create_response.json()

    # Verify the first member exists but is not a leader
    member1_headers = get_auth_headers_for_citizen(member1['id'])
    leader = (
        db_session.query(GroupLeader)
        .filter(
            GroupLeader.group_id == test_group.id,
            GroupLeader.citizen_id == member1['id'],
        )
        .first()
    )
    assert leader is None, 'Regular member should not be a leader'

    # Try to update the second member as a regular member
    update_data = {
        'first_name': 'Updated',
        'last_name': 'Name',
        'email': 'updated.email@example.com',
    }

    response = client.put(
        f'/groups/{test_group.id}/members/{member2["id"]}',
        json=update_data,
        headers=member1_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_member_success(client, db_session, auth_headers, test_group):
    """Test successfully deleting a member from a group"""
    # Verify the user is actually a leader of the group
    leader = (
        db_session.query(GroupLeader)
        .filter(
            GroupLeader.group_id == test_group.id,
            GroupLeader.citizen_id == test_group.leaders[0].id,
        )
        .first()
    )
    assert leader is not None, 'Test user should be a leader of the group'

    # First create a member
    member_data = {
        'first_name': 'Jane',
        'last_name': 'Smith',
        'email': 'jane.smith@example.com',
    }

    create_response = client.post(
        f'/groups/{test_group.id}/members',
        json=member_data,
        headers=auth_headers,
    )
    created_member = create_response.json()
    citizen_id = created_member['id']

    # Now delete the member
    response = client.delete(
        f'/groups/{test_group.id}/members/{citizen_id}',
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_member_unauthorized(client, test_group):
    """Test deleting a member without authentication"""
    response = client.delete(f'/groups/{test_group.id}/members/1')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_member_forbidden(client, create_test_citizen, test_group):
    """Test that non-leaders can't delete members"""
    non_leader = create_test_citizen(2)
    headers = get_auth_headers_for_citizen(non_leader.id)

    response = client.delete(
        f'/groups/{test_group.id}/members/1',
        headers=headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_member_as_regular_member(client, db_session, test_group):
    """Test that a regular member (non-leader) can't delete other members"""
    # First create two regular members using the leader's auth
    leader_headers = get_auth_headers_for_citizen(test_group.leaders[0].id)

    # Create first member
    member1_data = {
        'first_name': 'Regular',
        'last_name': 'Member',
        'email': 'regular.member@example.com',
    }
    create_response = client.post(
        f'/groups/{test_group.id}/members',
        json=member1_data,
        headers=leader_headers,
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    member1 = create_response.json()
    member1_id = member1['id']

    # Create second member
    member2_data = {
        'first_name': 'Another',
        'last_name': 'Member',
        'email': 'another.member@example.com',
    }
    create_response = client.post(
        f'/groups/{test_group.id}/members',
        json=member2_data,
        headers=leader_headers,
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    member2 = create_response.json()
    member2_id = member2['id']

    # Verify the first member exists but is not a leader
    member1_headers = get_auth_headers_for_citizen(member1_id)
    leader = (
        db_session.query(GroupLeader)
        .filter(
            GroupLeader.group_id == test_group.id,
            GroupLeader.citizen_id == member1_id,
        )
        .first()
    )
    assert leader is None, 'Regular member should not be a leader'

    # Try to delete the second member as a regular member
    response = client.delete(
        f'/groups/{test_group.id}/members/{member2_id}',
        headers=member1_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Verify the second member still exists
    response = client.get(f'/groups/{test_group.id}', headers=leader_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    member_ids = [member['id'] for member in data['members']]
    assert member2_id in member_ids, 'Member should not have been deleted'


def test_create_members_batch_success(client, db_session, auth_headers, test_group):
    """Test successfully creating multiple members in a batch"""
    batch_data = {
        'members': [
            {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com',
                'telegram': '@johndoe',
                'organization': 'Test Org',
                'role': 'member',
                'gender': 'male',
            },
            {
                'first_name': 'Jane',
                'last_name': 'Smith',
                'email': 'jane.smith@example.com',
                'telegram': '@janesmith',
                'organization': 'Test Org',
                'role': 'member',
                'gender': 'female',
            },
        ]
    }

    response = client.post(
        f'/groups/{test_group.id}/members/batch',
        json=batch_data,
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_207_MULTI_STATUS
    data = response.json()
    assert len(data) == 2

    # Check first member
    assert data[0]['success'] is True
    assert data[0]['err_msg'] is None
    assert data[0]['first_name'] == 'John'
    assert data[0]['email'] == 'john.doe@example.com'
    assert data[0]['id'] > 0

    # Check second member
    assert data[1]['success'] is True
    assert data[1]['err_msg'] is None
    assert data[1]['first_name'] == 'Jane'
    assert data[1]['email'] == 'jane.smith@example.com'
    assert data[1]['id'] > 0

    # Verify members were added to the group
    group = db_session.query(Group).filter(Group.id == test_group.id).first()
    assert len(group.members) == 2


def test_create_members_batch_partial_success(
    client, db_session, auth_headers, test_group
):
    """Test batch creation with some members failing"""
    # First create a member to test duplicate email
    existing_member_data = {
        'first_name': 'Existing',
        'last_name': 'Member',
        'email': 'existing@example.com',
    }
    client.post(
        f'/groups/{test_group.id}/members',
        json=existing_member_data,
        headers=auth_headers,
    )

    batch_data = {
        'members': [
            {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'existing@example.com',  # This should fail as email exists
                'telegram': '@johndoe',
            },
            {
                'first_name': 'Jane',
                'last_name': 'Smith',
                'email': 'jane.smith@example.com',  # This should succeed
                'telegram': '@janesmith',
            },
        ]
    }

    response = client.post(
        f'/groups/{test_group.id}/members/batch',
        json=batch_data,
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_207_MULTI_STATUS
    data = response.json()
    assert len(data) == 2

    # Check first member (should fail)
    assert data[0]['success'] is False
    assert data[0]['err_msg'] is not None
    assert data[0]['id'] == 0

    # Check second member (should succeed)
    assert data[1]['success'] is True
    assert data[1]['err_msg'] is None
    assert data[1]['id'] > 0
    assert data[1]['email'] == 'jane.smith@example.com'

    # Verify only one new member was added
    group = db_session.query(Group).filter(Group.id == test_group.id).first()
    assert len(group.members) == 2  # existing member + successful new member


def test_create_members_batch_validation(client, auth_headers, test_group):
    """Test batch creation with invalid member data"""
    batch_data = {
        'members': [
            {
                'first_name': '',  # Empty first name should fail validation
                'last_name': 'Doe',
                'email': 'john.doe@example.com',
            },
            {
                'first_name': 'Jane',
                'last_name': 'Smith',
                'email': 'invalid-email',  # Invalid email should fail validation
            },
        ]
    }

    response = client.post(
        f'/groups/{test_group.id}/members/batch',
        json=batch_data,
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_members_batch_empty_list(client, auth_headers, test_group):
    """Test batch creation with empty members list"""
    batch_data = {'members': []}

    response = client.post(
        f'/groups/{test_group.id}/members/batch',
        json=batch_data,
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_members_batch_unauthorized(client, test_group):
    """Test batch creation without authentication"""
    batch_data = {
        'members': [
            {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com',
            }
        ]
    }

    response = client.post(
        f'/groups/{test_group.id}/members/batch',
        json=batch_data,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_members_batch_forbidden(client, create_test_citizen, test_group):
    """Test batch creation by non-leader user"""
    non_leader = create_test_citizen(2)
    headers = get_auth_headers_for_citizen(non_leader.id)

    batch_data = {
        'members': [
            {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com',
            }
        ]
    }

    response = client.post(
        f'/groups/{test_group.id}/members/batch',
        json=batch_data,
        headers=headers,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
