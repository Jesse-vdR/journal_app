import os
import sys
import pytest
import uuid

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models import User

@pytest.fixture(scope='function')
def app():
    """Create and configure a new app instance for each test."""
    _app = create_app()
    _app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-key',
        'SERVER_NAME': 'localhost:5000'
    })
    
    # Create tables and context
    with _app.app_context():
        db.create_all()
        yield _app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def test_user(app):
    """Create a test user for the tests."""
    with app.app_context():
        unique_id = str(uuid.uuid4())
        username = f'test_{unique_id}'
        email = f'test_{unique_id}@example.com'
        
        user = User(username=username, email=email)
        user.set_password('test_password')
        db.session.add(user)
        db.session.commit()
        
        # Get a fresh instance from the database
        user = User.query.filter_by(username=username).first()
        
        # Store credentials in app config for tests
        app.config['TEST_USERNAME'] = username
        app.config['TEST_PASSWORD'] = 'test_password'
        
        yield user
        
        db.session.delete(user)
        db.session.commit()

@pytest.fixture
def auth_client(app, client):
    """Create a client that is already logged in."""
    with app.app_context():
        # Create a new user specifically for this client
        unique_id = str(uuid.uuid4())
        username = f'auth_user_{unique_id}'
        email = f'auth_{unique_id}@example.com'
        
        user = User(username=username, email=email)
        user.set_password('test_password')
        db.session.add(user)
        db.session.commit()
        
        # Login
        client.post('/auth/login', data={
            'username': username,
            'password': 'test_password'
        }, follow_redirects=True)
        
        yield client
        
        # Cleanup
        user = User.query.filter_by(username=username).first()
        if user:
            db.session.delete(user)
            db.session.commit()

@pytest.fixture(scope='module')
def flask_server():
    """Start Flask server in a separate thread for Selenium tests."""
    _app = create_app()
    
    # Use a persistent SQLite database for Selenium tests
    test_db_path = os.path.join(os.path.dirname(__file__), 'test.db')
    _app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{test_db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-key',
        'SERVER_NAME': 'localhost:5000'
    })
    
    with _app.app_context():
        db.create_all()
        
        # Create a test user for Selenium tests if it doesn't exist
        username = 'test_user'
        email = 'test@example.com'
        if not User.query.filter_by(username=username).first():
            user = User(username=username, email=email)
            user.set_password('test_password')
            db.session.add(user)
            db.session.commit()
    
    def run_server():
        _app.run(port=5000, use_reloader=False)
    
    import threading
    server = threading.Thread(target=run_server)
    server.daemon = True
    server.start()
    
    # Wait for server to start
    import time
    time.sleep(2)
    
    yield _app
    
    # Cleanup
    with _app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='module')
def chrome_driver():
    """Create a Chrome WebDriver instance."""
    from selenium import webdriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

@pytest.fixture(scope='module')
def selenium_user(flask_server):
    """Return the credentials for the Selenium test user."""
    return {
        'username': 'test_user',
        'password': 'new_test_password'
    }
