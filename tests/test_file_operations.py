import os
import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app import create_app, db
from app.models import User, FileMetadata
from werkzeug.security import generate_password_hash
import uuid
import json

@pytest.fixture(scope='session')
def selenium_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

@pytest.fixture(scope='function')
def test_client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['FILE_BROWSER_ROOT'] = os.path.join(os.path.dirname(__file__), 'test_uploads')
    
    # Create test upload directory
    os.makedirs(app.config['FILE_BROWSER_ROOT'], exist_ok=True)
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create test user with unique email
            unique_id = str(uuid.uuid4())
            user = User(
                username=f'test_{unique_id}', 
                email=f'test_{unique_id}@example.com'
            )
            user.set_password('test')
            db.session.add(user)
            db.session.commit()
            
            # Login
            client.post('/auth/login', data={
                'username': user.username,
                'password': 'test'
            }, follow_redirects=True)
            
        yield client
        
        # Cleanup
        with app.app_context():
            db.drop_all()
        
        # Remove test files
        for root, dirs, files in os.walk(app.config['FILE_BROWSER_ROOT']):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                os.rmdir(os.path.join(root, d))
        os.rmdir(app.config['FILE_BROWSER_ROOT'])

def login(driver, base_url):
    driver.get(f"{base_url}/auth/login")
    username_input = driver.find_element(By.ID, "username")
    password_input = driver.find_element(By.ID, "password")
    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    
    username_input.send_keys("test")
    password_input.send_keys("test")
    submit_button.click()
    
    # Wait for redirect
    WebDriverWait(driver, 10).until(
        EC.url_to_be(f"{base_url}/")
    )

def test_file_upload(test_client):
    """Test file upload functionality"""
    try:
        # Create test file
        test_file_path = os.path.join(os.path.dirname(__file__), 'test_file.txt')
        with open(test_file_path, 'w') as f:
            f.write('Test content')
        
        # Verify test file was created
        assert os.path.exists(test_file_path), "Test file was not created"
        
        # Upload file
        with open(test_file_path, 'rb') as f:
            response = test_client.post('/files/api/upload', 
                data={
                    'file': (f, 'test_file.txt'),
                    'path': '/'
                },
                content_type='multipart/form-data'
            )
        
        # Print response for debugging
        print(f"Upload response status: {response.status_code}")
        print(f"Upload response data: {response.data.decode('utf-8')}")
        
        assert response.status_code == 200, f"Upload failed with status {response.status_code}"
        data = json.loads(response.data)
        assert 'message' in data, "Response missing 'message' field"
        assert data['message'] == 'File uploaded successfully'
        
        # Verify file exists in upload directory
        uploaded_file = os.path.join(test_client.application.config['FILE_BROWSER_ROOT'], 'test_file.txt')
        assert os.path.exists(uploaded_file), "Uploaded file not found in target directory"
        
        # Verify file contents
        with open(uploaded_file, 'r') as f:
            content = f.read()
        assert content == 'Test content', "Uploaded file contents do not match"
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        # Print current directory contents
        print("Current directory contents:")
        test_dir = test_client.application.config['FILE_BROWSER_ROOT']
        if os.path.exists(test_dir):
            for root, dirs, files in os.walk(test_dir):
                print(f"Directory: {root}")
                print(f"Files: {files}")
        else:
            print(f"Test directory {test_dir} does not exist")
        raise
    finally:
        # Cleanup test file
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)

def test_create_folder(test_client):
    """Test folder creation functionality"""
    try:
        # Create folder
        response = test_client.post('/files/api/create_folder',
            data={
                'path': '/',
                'name': 'test_folder'
            }
        )
        
        # Print response for debugging
        print(f"Create folder response status: {response.status_code}")
        print(f"Create folder response data: {response.data.decode('utf-8')}")
        
        assert response.status_code == 200, f"Create folder failed with status {response.status_code}"
        data = json.loads(response.data)
        assert 'message' in data, "Response missing 'message' field"
        assert data['message'] == 'Folder created successfully'
        
        # Verify folder exists
        folder_path = os.path.join(test_client.application.config['FILE_BROWSER_ROOT'], 'test_folder')
        assert os.path.exists(folder_path), "Created folder not found"
        assert os.path.isdir(folder_path), "Created path is not a directory"
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        # Print current directory contents
        print("Current directory contents:")
        test_dir = test_client.application.config['FILE_BROWSER_ROOT']
        if os.path.exists(test_dir):
            for root, dirs, files in os.walk(test_dir):
                print(f"Directory: {root}")
                print(f"Files: {files}")
        else:
            print(f"Test directory {test_dir} does not exist")
        raise

def test_delete_file(test_client):
    """Test file deletion functionality"""
    try:
        # Create test file
        test_file_path = os.path.join(test_client.application.config['FILE_BROWSER_ROOT'], 'test_delete.txt')
        with open(test_file_path, 'w') as f:
            f.write('Test content')
        
        # Verify test file was created
        assert os.path.exists(test_file_path), "Test file was not created"
        
        # Delete file
        response = test_client.post('/files/api/delete',
            data={
                'path': '/test_delete.txt'
            }
        )
        
        # Print response for debugging
        print(f"Delete response status: {response.status_code}")
        print(f"Delete response data: {response.data.decode('utf-8')}")
        
        assert response.status_code == 200, f"Delete failed with status {response.status_code}"
        data = json.loads(response.data)
        assert 'message' in data, "Response missing 'message' field"
        assert data['message'] == 'File deleted successfully'
        
        # Verify file was deleted
        assert not os.path.exists(test_file_path), "File still exists after deletion"
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        # Print current directory contents
        print("Current directory contents:")
        test_dir = test_client.application.config['FILE_BROWSER_ROOT']
        if os.path.exists(test_dir):
            for root, dirs, files in os.walk(test_dir):
                print(f"Directory: {root}")
                print(f"Files: {files}")
        else:
            print(f"Test directory {test_dir} does not exist")
        raise
