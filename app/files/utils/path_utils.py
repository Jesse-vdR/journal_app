from flask import current_app
from flask_login import current_user
import os

def normalize_path(path):
    """Normalize a path by removing trailing slashes and converting None to empty string"""
    if path is None or path == '':
        return ''
    # Convert Windows backslashes to forward slashes
    return path.replace('\\', '/').rstrip('/')

def get_user_base_dir():
    """Get the base directory for the current user's files"""
    base_dir = os.path.join(current_app.static_folder, 'uploads', str(current_user.id))
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    return base_dir

def get_safe_path(base_dir, path):
    """Get a safe absolute path within base_dir"""
    # Convert to absolute path and normalize
    if not path:
        return base_dir
    
    # Convert path to use forward slashes
    path = path.replace('\\', '/')
    abs_path = os.path.abspath(os.path.join(base_dir, path))
    
    # Check if the path is within base_dir
    if not abs_path.startswith(base_dir):
        return None
    
    return abs_path
