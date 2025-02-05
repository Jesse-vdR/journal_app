from app import create_app, db
from app.models import User
import os

def reset_database():
    app = create_app()
    
    with app.app_context():
        # Get the absolute path to the project directory
        project_dir = os.path.abspath(os.path.dirname(__file__))
        db_path = os.path.join(project_dir, 'app.db')
        
        # Remove existing database
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Removed existing database: {db_path}")
        
        # Create new database
        db.create_all()
        print("Created new database tables")
        
        # Create a test user
        user = User(username='test', email='test@example.com')
        user.set_password('test')
        db.session.add(user)
        db.session.commit()
        print(f"Created test user: username='test', password='test'")

if __name__ == '__main__':
    reset_database()
