import pytest
from app import create_app
from app.extensions import db as _db
from app.config import TestingConfig

@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app(TestingConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()

@pytest.fixture(scope='function')
def db(app):
    """Database fixture that cleans up after each test."""
    _db.create_all()
    yield _db
    _db.session.rollback()
    _db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    """Test client."""
    return app.test_client()

@pytest.fixture(scope='function')
def auth_headers(client):
    """Create authenticated user and return headers."""
    from app.models.user import User
    from app.extensions import db
    
    user = User(
        email='test@test.com',
        username='testuser',
        display_name='Test User'
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()

    response = client.post('/api/auth/login', json={
        'email': 'test@test.com',
        'password': 'password123'
    })
    token = response.json['data']['access_token']
    return {'Authorization': f'Bearer {token}'}
