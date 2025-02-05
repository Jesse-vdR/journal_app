import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from threading import Thread
from time import sleep
from app import create_app, db
from app.models import User
import uuid
import requests

@pytest.fixture(scope='module')
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SERVER_NAME': 'localhost:5000',
        'LOGIN_DISABLED': True
    })
    yield app

@pytest.fixture(scope='module')
def flask_server(app):
    """Start Flask server in a separate thread"""
    def run_server():
        app.run(port=5000, use_reloader=False)
    
    server = Thread(target=run_server)
    server.daemon = True
    server.start()
    # Wait for server to start
    sleep(1)
    yield
    # Cleanup will happen automatically since it's a daemon thread

@pytest.fixture(scope='module')
def chrome_driver():
    """Setup Chrome WebDriver with appropriate options"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)  # Wait up to 10 seconds for elements
    yield driver
    driver.quit()

@pytest.fixture(scope='module')
def selenium_user():
    return {
        'username': 'test_user',
        'password': 'test_password'
    }

def test_home_page_elements(chrome_driver, flask_server):
    """Test that main page elements are present"""
    chrome_driver.get('http://localhost:5000/')
    
    # Check title
    assert "AI Website" in chrome_driver.title
    
    # Check navigation elements
    nav = chrome_driver.find_element(By.TAG_NAME, 'nav')
    assert 'Home' in nav.text
    assert 'Login' in nav.text
    assert 'Register' in nav.text

def test_login_flow(chrome_driver, flask_server, selenium_user):
    """Test the login process"""
    chrome_driver.get('http://localhost:5000/auth/login')
    
    # Fill in login form
    username_field = chrome_driver.find_element(By.ID, 'username')
    password_field = chrome_driver.find_element(By.ID, 'password')
    submit_button = chrome_driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]')
    
    username_field.send_keys(selenium_user['username'])
    password_field.send_keys(selenium_user['password'])
    submit_button.click()
    
    # Wait for redirect and check we're logged in
    try:
        welcome_text = WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'flash'))
        )
        assert 'Welcome' in welcome_text.text
    except TimeoutException:
        pytest.fail("Login redirect failed or welcome message not found")

def test_file_upload_interface(chrome_driver, flask_server, selenium_user):
    """Test the file upload interface is working"""
    # First login
    chrome_driver.get('http://localhost:5000/auth/login')
    username_field = chrome_driver.find_element(By.ID, 'username')
    password_field = chrome_driver.find_element(By.ID, 'password')
    submit_button = chrome_driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]')
    
    username_field.send_keys(selenium_user['username'])
    password_field.send_keys(selenium_user['password'])
    submit_button.click()
    
    # Navigate to file browser
    chrome_driver.get('http://localhost:5000/files/browse')
    
    # Check for upload elements
    try:
        # Wait for page to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.ID, 'file-list'))
        )
        
        upload_button = chrome_driver.find_element(By.CSS_SELECTOR, '[data-bs-target="#upload-modal"]')
        assert upload_button.is_displayed()
        
        # Open upload modal
        upload_button.click()
        
        # Wait for modal to open
        WebDriverWait(chrome_driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'upload-modal'))
        )
        
        file_input = chrome_driver.find_element(By.ID, 'file-input')
        assert file_input.get_attribute('type') == 'file'
    except TimeoutException:
        pytest.fail("File upload interface elements not found")

def test_responsive_design(chrome_driver, flask_server):
    """Test that the site is responsive"""
    chrome_driver.get('http://localhost:5000/')
    
    # Test different viewport sizes
    viewports = [
        (1920, 1080),  # Desktop
        (768, 1024),   # Tablet
        (375, 812)     # Mobile
    ]
    
    for width, height in viewports:
        chrome_driver.set_window_size(width, height)
        sleep(0.5)  # Allow time for responsive changes
        
        # Check that navigation is visible
        nav = chrome_driver.find_element(By.TAG_NAME, 'nav')
        assert nav.is_displayed()
        
        # On mobile, check for hamburger menu
        if width <= 768:
            try:
                menu_button = chrome_driver.find_element(By.CLASS_NAME, 'navbar-toggler')
                assert menu_button.is_displayed()
            except:
                pytest.fail(f"Hamburger menu not found at viewport size {width}x{height}")
