import os
import pytest
from pathlib import Path
from flask import current_app
from werkzeug.datastructures import FileStorage
from io import BytesIO

def login(client, username='test_user', password='test_password'):
    return client.post('/auth/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)

def test_file_browser_access(auth_client):
    """Test that the file browser page is accessible"""
    response = auth_client.get('/files/browse')
    assert response.status_code == 200
    assert b'Upload Files' in response.data

def test_list_files(auth_client):
    """Test listing files API"""
    response = auth_client.get('/files/api/files?path=/')
    assert response.status_code == 200
    data = response.get_json()
    assert 'items' in data
    assert isinstance(data['items'], list)

def test_upload_file(auth_client, tmp_path):
    """Test file upload functionality"""
    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test content")
    
    with open(test_file, 'rb') as f:
        response = auth_client.post('/files/api/upload', data={
            'file': (f, 'test.txt'),
            'path': '/'
        })
    assert response.status_code == 200
    
    # Verify file appears in listing
    response = auth_client.get('/files/api/files?path=/')
    assert response.status_code == 200
    data = response.get_json()
    assert any(item['name'] == 'test.txt' for item in data['items'])

def test_download_file(auth_client, tmp_path):
    """Test file download functionality"""
    # First upload a file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test content")
    
    with open(test_file, 'rb') as f:
        auth_client.post('/files/api/upload', data={
            'file': (f, 'test.txt'),
            'path': '/'
        })
    
    # Now try to download it
    response = auth_client.get('/files/api/download?path=/test.txt')
    assert response.status_code == 200
    assert response.data == b"Test content"

def test_security_checks(auth_client):
    """Test security measures for file operations"""
    # Test path traversal prevention
    response = auth_client.get('/files/api/files?path=/../')
    assert response.status_code == 400
    
    response = auth_client.get('/files/api/download?path=/../etc/passwd')
    assert response.status_code == 400
    
    # Test invalid paths
    response = auth_client.get('/files/api/files?path=nonexistent')
    assert response.status_code == 404
