import os
import tempfile
import pytest
from app import create_app, db
from app.models import User

@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False
    })

    with app.app_context():
        db.create_all()
        yield app

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def test_user(app):
    with app.app_context():
        # Clean up any existing users
        User.query.delete()
        db.session.commit()
        
        # Create new test user
        user = User(username='test_user', email='test@example.com')
        user.set_password('test_password')
        db.session.add(user)
        db.session.commit()
        return user
