import os
from dotenv import load_dotenv
from pathlib import Path

# Load the environment variables from .env file
basedir = os.path.abspath(os.path.dirname(__file__))
env_file = os.path.join(basedir, '.env')
load_dotenv(env_file)

class Config:
    # Flask and extensions
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File browser settings
    FILE_BROWSER_ROOT = os.path.join(basedir, 'app', 'static', 'uploads')
    FILE_BROWSER_ALLOWED_EXTENSIONS = {
        # Documents
        'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'md', 'rtf',
        # Images
        'png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg', 'webp',
        # Web files
        'html', 'css', 'js', 'json', 'xml',
        # Programming
        'py', 'java', 'cpp', 'c', 'h', 'hpp', 'cs', 'rb', 'php',
        # Archives
        'zip', 'rar', '7z', 'tar', 'gz',
        # Audio
        'mp3', 'wav', 'ogg', 'm4a',
        # Video
        'mp4', 'avi', 'mkv', 'mov', 'webm'
    }
    
    # Weather settings
    OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY')
    WEATHER_CITY = os.environ.get('WEATHER_CITY', 'Utrecht')
    
    def __init__(self):
        # Print debug info for environment variables
        print("\n=== Environment Variables Debug ===")
        print(f"Config file location: {basedir}")
        print(f".env file location: {env_file}")
        print(f".env file exists: {os.path.exists(env_file)}")
        print(f"OPENWEATHER_API_KEY configured: {'Yes' if self.OPENWEATHER_API_KEY else 'No'}")
        if self.OPENWEATHER_API_KEY:
            print(f"API Key: {self.OPENWEATHER_API_KEY}")
        
        # Ensure the file browser root directory exists
        os.makedirs(self.FILE_BROWSER_ROOT, exist_ok=True)
        
        # Create a .gitkeep file to ensure the directory is tracked by git
        gitkeep_file = os.path.join(self.FILE_BROWSER_ROOT, '.gitkeep')
        if not os.path.exists(gitkeep_file):
            with open(gitkeep_file, 'w') as f:
                pass
