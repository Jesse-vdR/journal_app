from dotenv import load_dotenv
import os
import requests
import socket

# Load environment variables from .env file
print("\nLoading environment variables...")
load_dotenv()

# Debug: Check if API key is loaded
api_key = os.environ.get('OPENWEATHER_API_KEY')
print(f"API Key loaded: {'Yes' if api_key else 'No'}")
if api_key:
    print(f"API Key length: {len(api_key)}")
    print(f"API Key first/last chars: {api_key[:4]}...{api_key[-4:]}")

from app import create_app, db
from app.models import User
from sqlalchemy import inspect

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}

if __name__ == '__main__':
    with app.app_context():
        # Debug database information
        print("\n=== Database Information ===")
        inspector = inspect(db.engine)
        
        # Check if tables exist
        tables = inspector.get_table_names()
        print(f"Tables in database: {tables}")
        
        # Check if any users exist
        user_count = User.query.count()
        print(f"Number of users in database: {user_count}")
        
        # Check database connection
        try:
            db.session.execute('SELECT 1')
            print("Database connection: OK")
        except Exception as e:
            print(f"Database connection error: {e}")
            
        # Get local IP for network access
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"\nLocal IP address: {local_ip}")
        
    app.run(debug=True, host='0.0.0.0')
