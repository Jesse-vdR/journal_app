import pytest
from flask import session
from app.models import User

def test_register(client, app):
    """Test user registration functionality"""
    # Test GET request
    response = client.get('/auth/register')
    assert response.status_code == 200
    assert b'Register' in response.data

    # Test successful registration
    response = client.post('/auth/register', data={
        'username': 'new_user',
        'email': 'new@example.com',
        'password': 'new_password',
        'password2': 'new_password'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Congratulations, you are now a registered user!' in response.data

    # Verify user was created
    with app.app_context():
        user = User.query.filter_by(username='new_user').first()
        assert user is not None
        assert user.email == 'new@example.com'
        assert user.check_password('new_password')

def test_register_validation(client, app, test_user):
    """Test registration validation rules"""
    with app.app_context():
        # Get fresh user instance
        user = User.query.filter_by(username=test_user.username).first()
        
        # Test duplicate username
        response = client.post('/auth/register', data={
            'username': user.username,
            'email': 'another@example.com',
            'password': 'password',
            'password2': 'password'
        }, follow_redirects=True)
        assert b'Please use a different username' in response.data

        # Test invalid email format
        response = client.post('/auth/register', data={
            'username': 'valid_user',
            'email': 'invalid-email',
            'password': 'password',
            'password2': 'password'
        }, follow_redirects=True)
        assert b'Invalid email address' in response.data

        # Test password mismatch
        response = client.post('/auth/register', data={
            'username': 'valid_user',
            'email': 'valid@example.com',
            'password': 'password1',
            'password2': 'password2'
        }, follow_redirects=True)
        assert b'Passwords must match' in response.data

def test_login_logout(client, app, test_user):
    """Test login and logout functionality"""
    with app.app_context():
        # Get fresh user instance
        user = User.query.filter_by(username=test_user.username).first()
        
        # Test login
        response = client.post('/auth/login', data={
            'username': user.username,
            'password': 'test_password'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Welcome' in response.data

        # Test logout
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'Sign In' in response.data

def test_login_validation(client, app, test_user):
    """Test login validation rules"""
    with app.app_context():
        # Get fresh user instance
        user = User.query.filter_by(username=test_user.username).first()
        
        # Test invalid username
        response = client.post('/auth/login', data={
            'username': 'wrong_user',
            'password': 'test_password'
        }, follow_redirects=True)
        assert b'Invalid username or password' in response.data

        # Test invalid password
        response = client.post('/auth/login', data={
            'username': user.username,
            'password': 'wrong_password'
        }, follow_redirects=True)
        assert b'Invalid username or password' in response.data

def test_protected_routes(client, app, test_user):
    """Test access control on protected routes"""
    with app.app_context():
        # Get fresh user instance
        user = User.query.filter_by(username=test_user.username).first()
        
        # Test access to protected route without login
        response = client.get('/files/browse', follow_redirects=True)
        assert b'Sign In' in response.data

        # Login
        client.post('/auth/login', data={
            'username': user.username,
            'password': 'test_password'
        })

        # Test access to protected route after login
        response = client.get('/files/browse')
        assert response.status_code == 200
        assert b'Upload Files' in response.data
