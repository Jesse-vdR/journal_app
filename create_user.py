from app import create_app, db
from app.models import User

def create_test_user():
    app = create_app()
    with app.app_context():
        # Create all database tables
        db.create_all()
        
        # Check if user already exists
        user = User.query.filter_by(username='admin').first()
        if user is None:
            # Create new user
            user = User(username='admin', email='admin@example.com')
            user.set_password('admin123')
            db.session.add(user)
            db.session.commit()
            print("Created new user:")
        else:
            print("User already exists:")
        print(f"Username: admin")
        print(f"Password: admin123")

if __name__ == '__main__':
    create_test_user()
