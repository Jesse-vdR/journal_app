from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    # Create all database tables
    db.create_all()
    
    # Create a test user if it doesn't exist
    user = User.query.filter_by(username='test').first()
    if not user:
        user = User(
            username='test',
            email='test@example.com',
            storage_used=0,
            storage_limit=1024 * 1024 * 100  # 100MB default storage limit
        )
        user.set_password('test')
        db.session.add(user)
        db.session.commit()
        print("Created test user:")
        print(f"Username: test")
        print(f"Password: test")
        print(f"Storage limit: 100MB")
    else:
        print("Test user already exists")
