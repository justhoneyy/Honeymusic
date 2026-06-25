"""Tests for authentication endpoints."""

def test_register(client):
    """Test user registration."""
    response = client.post('/api/auth/register', json={
        'email': 'newuser@test.com',
        'username': 'newuser',
        'password': 'password123'
    })
    assert response.status_code == 201
    assert 'access_token' in response.json['data']

def test_register_duplicate_email(client):
    """Test registration with duplicate email."""
    client.post('/api/auth/register', json={
        'email': 'dup@test.com',
        'username': 'user1',
        'password': 'password123'
    })
    response = client.post('/api/auth/register', json={
        'email': 'dup@test.com',
        'username': 'user2',
        'password': 'password123'
    })
    assert response.status_code == 409

def test_login_success(client):
    """Test successful login."""
    client.post('/api/auth/register', json={
        'email': 'login@test.com',
        'username': 'loginuser',
        'password': 'password123'
    })
    response = client.post('/api/auth/login', json={
        'email': 'login@test.com',
        'password': 'password123'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json['data']

def test_login_invalid_password(client):
    """Test login with wrong password."""
    response = client.post('/api/auth/login', json={
        'email': 'nonexistent@test.com',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401

def test_get_me_authenticated(client, auth_headers):
    """Test getting current user when authenticated."""
    response = client.get('/api/auth/me', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['data']['email'] == 'test@test.com'

def test_get_me_unauthenticated(client):
    """Test getting current user without auth."""
    response = client.get('/api/auth/me')
    assert response.status_code == 401
