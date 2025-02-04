import pytest
from flask import session
from app.models import User

def test_register(client, app):
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

def test_register_validation(client, test_user):
    # Test duplicate username
    response = client.post('/auth/register', data={
        'username': 'test_user',  # This username is created in conftest.py
        'email': 'another@example.com',
        'password': 'password',
        'password2': 'password'
    }, follow_redirects=False)
    assert response.status_code == 200  # Should stay on register page
    assert b'Please use a different username' in response.data

    # Test invalid email format
    response = client.post('/auth/register', data={
        'username': 'valid_user',
        'email': 'invalid-email',
        'password': 'password',
        'password2': 'password'
    })
    assert b'Invalid email address' in response.data

    # Test password mismatch
    response = client.post('/auth/register', data={
        'username': 'valid_user',
        'email': 'valid@example.com',
        'password': 'password1',
        'password2': 'password2'
    })
    assert b'Field must be equal to password' in response.data

def test_login_logout(client, test_user):
    # Test successful login
    response = client.post('/auth/login', data={
        'username': 'test_user',
        'password': 'test_password',
        'remember_me': False
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Welcome, test_user!' in response.data

    # Test logout
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Sign In' in response.data

def test_login_validation(client, test_user):
    # Test invalid username
    response = client.post('/auth/login', data={
        'username': 'wrong_user',
        'password': 'test_password'
    }, follow_redirects=True)
    assert b'Invalid username or password' in response.data

    # Test invalid password
    response = client.post('/auth/login', data={
        'username': 'test_user',
        'password': 'wrong_password'
    }, follow_redirects=True)
    assert b'Invalid username or password' in response.data

def test_protected_routes(client, test_user):
    # Test accessing protected page without login
    response = client.get('/', follow_redirects=True)
    assert b'Sign In' in response.data

    # Login and verify session
    response = client.post('/auth/login', data={
        'username': 'test_user',
        'password': 'test_password'
    }, follow_redirects=True)
    assert b'Welcome' in response.data

    # Test accessing protected page after login
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b'Welcome' in response.data
