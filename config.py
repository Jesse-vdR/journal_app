import os
from dotenv import load_dotenv
from pathlib import Path

class Config:
    # Flask and extensions
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # SQLAlchemy
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File browser settings
    FILE_BROWSER_ROOT = os.path.join(basedir, 'app', 'static', 'uploads')
    FILE_BROWSER_ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'py', 'html', 'css', 'js'}
    
    def __init__(self):
        # Ensure the file browser root directory exists
        os.makedirs(self.FILE_BROWSER_ROOT, exist_ok=True)
        
        # Create a .gitkeep file to ensure the directory is tracked by git
        gitkeep_file = os.path.join(self.FILE_BROWSER_ROOT, '.gitkeep')
        if not os.path.exists(gitkeep_file):
            with open(gitkeep_file, 'w') as f:
                pass
