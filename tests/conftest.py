import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import create_app
from app.extensions import db as _db
from app.models.auth import Role, User, UserProfile
from app.services.seed_data import seed_database

class TestConfig:
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False

@pytest.fixture(scope='session')
def app():
    """Create application instance configured for testing with an in-memory DB."""
    app = create_app(TestConfig)
    import jinja2
    app.jinja_env.undefined = jinja2.StrictUndefined  # make template typos fail loudly
    with app.app_context():
        _db.create_all()
        seed_database()
        yield app
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def client(app):
    """Test client (clears Flask-Login's cached user so each test logs in fresh)."""
    from flask import g
    g.pop('_login_user', None)
    return app.test_client()

@pytest.fixture
def runner(app):
    """CLI runner."""
    return app.test_cli_runner()

@pytest.fixture
def db_session(app):
    """Provide a scoped db session that rolls back after test."""
    connection = _db.engine.connect()
    transaction = connection.begin()
    session = _db.scoped_session(lambda: _db.session)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

def login_user(client, email, password):
    """Helper to log in a user by posting to /auth/login."""
    return client.post('/auth/login', data={
        'username_or_email': email,
        'password': password
    }, follow_redirects=True)

@pytest.fixture
def admin_client(client):
    """Client authenticated as the default Admin user."""
    login_user(client, 'admin@hospital.com', 'Admin@123')
    return client

@pytest.fixture
def doctor_client(client):
    """Client authenticated as the Doctor user."""
    login_user(client, 'sarah.ahmed@hospital.com', 'Doctor@123')
    return client

@pytest.fixture
def nurse_client(client):
    """Client authenticated as the Nurse user."""
    login_user(client, 'nurse.fatima@hospital.com', 'Nurse@123')
    return client

@pytest.fixture
def receptionist_client(client):
    login_user(client, 'reception@hospital.com', 'Reception@123')
    return client

@pytest.fixture
def pharmacist_client(client):
    login_user(client, 'pharma@hospital.com', 'Pharma@123')
    return client

@pytest.fixture
def labtech_client(client):
    login_user(client, 'lab@hospital.com', 'Lab@123')
    return client
