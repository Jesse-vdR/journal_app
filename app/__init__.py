import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from .filters import datetime_filter

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configure logging
    app.logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)
    
    # Log database configuration
    app.logger.info(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Set default FILE_BROWSER_ROOT if not configured
    if 'FILE_BROWSER_ROOT' not in app.config:
        app.config['FILE_BROWSER_ROOT'] = os.path.expanduser('~')
    
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    
    # Register filters
    app.jinja_env.filters['datetime'] = datetime_filter
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.files import init_app as init_files
    init_files(app)

    from app.monitor import init_app as init_monitor
    init_monitor(app)

    from app.scripts import bp as scripts_bp, init_app as init_scripts
    app.register_blueprint(scripts_bp)
    init_scripts(app)

    from app.weather import bp as weather_bp
    app.register_blueprint(weather_bp)

    from app.accounts import bp as accounts_bp
    app.register_blueprint(accounts_bp)

    app.logger.info("Application started")
    
    # Ensure upload directory exists
    os.makedirs(app.config['FILE_BROWSER_ROOT'], exist_ok=True)
    
    return app

from app import models
