from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Create a test user
    username = 'testuser'
    password = 'testpass123'
    email = 'testuser@example.com'
    
    # Check if user already exists
    user = User.query.filter_by(username=username).first()
    if user is None:
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"\nCreated new test user:")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"Email: {email}")
    else:
        print("\nTest user already exists")
