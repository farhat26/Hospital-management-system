import pytest
from app.models.auth import User, Role, LoginHistory
from app.extensions import db

def test_password_hashing(app):
    """Test secure password hashing with werkzeug."""
    with app.app_context():
        user = User(username='test_crypto', email='crypto@hospital.com')
        user.set_password('SecretPassword@123')
        assert user.password_hash is not None
        assert user.password_hash != 'SecretPassword@123'
        assert user.check_password('SecretPassword@123') is True
        assert user.check_password('WrongPassword') is False

def test_admin_login_success(client):
    """Test successful login with admin credentials."""
    response = client.post('/auth/login', data={
        'username_or_email': 'admin@hospital.com',
        'password': 'Admin@123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert (b'Welcome back' in response.data) or (b'Dashboard' in response.data)

def test_login_invalid_password(client):
    """Test login failure with invalid password."""
    client.get('/auth/logout')
    response = client.post('/auth/login', data={
        'username_or_email': 'admin@hospital.com',
        'password': 'TotallyWrongPassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid username/email or password' in response.data

def test_role_based_access_admin_route(app, client):
    """Test that unauthorized users are rejected from admin endpoints."""
    # Ensure client is logged out first
    client.get('/auth/logout')
    
    # Test unauthenticated access -> redirects to login
    response = client.get('/admin/', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth/login' in response.headers.get('Location', '')

    # Login as Doctor (non-admin role)
    client.post('/auth/login', data={
        'username_or_email': 'sarah.ahmed@hospital.com',
        'password': 'Doctor@123'
    }, follow_redirects=True)

    # Doctor accessing admin panel should be denied (redirected to dashboard with warning)
    admin_resp = client.get('/admin/', follow_redirects=True)
    assert admin_resp.status_code == 200
    assert b'Access denied' in admin_resp.data

def test_logout(client):
    """Test logout clears session."""
    client.post('/auth/login', data={
        'username_or_email': 'admin@hospital.com',
        'password': 'Admin@123'
    }, follow_redirects=True)

    logout_resp = client.get('/auth/logout', follow_redirects=True)
    assert logout_resp.status_code == 200
    assert b'logged out' in logout_resp.data.lower() or b'sign in' in logout_resp.data.lower()
