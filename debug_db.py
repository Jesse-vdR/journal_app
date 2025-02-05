from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Check if any users exist
    users = User.query.all()
    print("\nRegistered Users:")
    print("-----------------")
    for user in users:
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print("-----------------")
