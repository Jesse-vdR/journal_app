from app import create_app, db
from app.models import User
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = create_app()

with app.app_context():
    print("\nDatabase URL:", app.config['SQLALCHEMY_DATABASE_URI'])
    print("Database file exists:", os.path.exists("app.db"))
    print("Database file path:", os.path.abspath("app.db"))
    
    # Check if tables exist
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    print("\nDatabase tables:", inspector.get_table_names())
    
    print("\nRegistered Users:")
    users = User.query.all()
    if users:
        for user in users:
            print(f"Username: {user.username}, Email: {user.email}")
    else:
        print("No users found in database")
