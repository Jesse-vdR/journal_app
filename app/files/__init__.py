from flask import Blueprint

bp = Blueprint('files', __name__, url_prefix='/files')

def init_user_directories():
    from app.models import User
    from app import db
    import os
    
    users = User.query.all()
    for user in users:
        user_dir = user.get_home_directory()
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)

def init_app(app):
    from app.files.views import routes
    from app.files.api import bp as api_bp
    
    app.register_blueprint(bp)
    app.register_blueprint(api_bp)
    
    with app.app_context():
        init_user_directories()
