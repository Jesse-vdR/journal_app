from app import create_app, db
from app.models import User

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}

if __name__ == '__main__':
    # Create all database tables
    with app.app_context():
        db.create_all()
        
        # Create test user if it doesn't exist
        if not User.query.filter_by(username='test').first():
            user = User(username='test', email='test@example.com')
            user.set_password('test')
            db.session.add(user)
            db.session.commit()
    
    # Run the app on all network interfaces
    app.run(host='0.0.0.0', port=5000, debug=True)
