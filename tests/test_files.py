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

def test_file_browser_access(client, test_user):
    # Test access without login
    response = client.get('/files/browse')
    assert response.status_code == 302  # Redirect to login
    
    # Login
    login_response = login(client)
    assert login_response.status_code == 200
    
    # Test access after login
    response = client.get('/files/browse')
    assert response.status_code == 200
    assert b'File Browser' in response.data

def test_list_files(client, test_user, tmp_path):
    # Login
    login_response = login(client)
    assert login_response.status_code == 200
    
    # Create test files and directories
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    # Configure app to use temp directory
    current_app.config['FILE_BROWSER_ROOT'] = str(tmp_path)
    
    # Test listing files
    response = client.get('/files/api/files')
    assert response.status_code == 200
    data = response.get_json()
    
    # Verify response structure
    assert 'current_path' in data
    assert 'items' in data
    
    # Verify files are listed
    items = {item['name']: item for item in data['items']}
    assert 'test_dir' in items
    assert items['test_dir']['type'] == 'directory'
    assert 'test.txt' in items
    assert items['test.txt']['type'] == 'file'

def test_upload_file(client, test_user, tmp_path):
    # Login
    login_response = login(client)
    assert login_response.status_code == 200
    
    # Configure app to use temp directory
    current_app.config['FILE_BROWSER_ROOT'] = str(tmp_path)
    
    # Create test file
    data = {'file': (BytesIO(b'test content'), 'test.txt')}
    
    # Test file upload
    response = client.post('/files/api/upload', 
                         data=data,
                         content_type='multipart/form-data')
    assert response.status_code == 200
    
    # Verify file was created
    uploaded_file = tmp_path / 'test.txt'
    assert uploaded_file.exists()
    assert uploaded_file.read_text() == 'test content'

def test_download_file(client, test_user, tmp_path):
    # Login
    login_response = login(client)
    assert login_response.status_code == 200
    
    # Configure app to use temp directory
    current_app.config['FILE_BROWSER_ROOT'] = str(tmp_path)
    
    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    # Test file download
    response = client.get(f'/files/api/download?path={str(test_file)}')
    assert response.status_code == 200
    assert response.data == b'test content'
    assert response.headers['Content-Disposition'] == 'attachment; filename=test.txt'

def test_security_checks(client, test_user, tmp_path):
    # Login
    login_response = login(client)
    assert login_response.status_code == 200
    
    # Configure app to use temp directory
    current_app.config['FILE_BROWSER_ROOT'] = str(tmp_path)
    
    # Test directory traversal attempt
    response = client.get('/files/api/files?path=../../../etc/passwd')
    assert response.status_code == 403
    
    # Test upload with invalid file type
    data = {'file': (BytesIO(b'malicious content'), 'malicious.exe')}
    response = client.post('/files/api/upload',
                         data=data,
                         content_type='multipart/form-data')
    assert response.status_code == 400
    
    # Test download with invalid path
    response = client.get('/files/api/download?path=../../../etc/passwd')
    assert response.status_code == 403
