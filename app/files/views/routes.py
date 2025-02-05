from flask import render_template, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
import os
from app.files import bp
from datetime import datetime

def get_storage_info():
    """Helper function to get storage info for the current user"""
    storage_used = current_user.storage_used
    storage_limit = current_user.storage_limit
    return {
        'storage_used': storage_used,
        'storage_limit': storage_limit,
        'storage_used_mb': round(storage_used / (1024 * 1024), 2),
        'storage_limit_mb': round(storage_limit / (1024 * 1024), 2)
    }

@bp.route('/')
@bp.route('/browse')
@bp.route('/browse/<path:path>')
@login_required
def browse(path=None):
    try:
        # Get user's home directory
        user_dir = current_user.get_home_directory()
        
        # Clean up path to prevent directory traversal
        if path:
            path = path.strip('/')
            
        # If no path specified or empty path, show root directory
        if not path:
            current_dir = ''
            full_path = user_dir
            parent_dir = None
        else:
            current_dir = path
            full_path = os.path.join(user_dir, path)
            # Get parent directory, but don't go above user's home directory
            parent_path = os.path.dirname(path)
            parent_dir = parent_path if parent_path else ''
            
            # Security check - make sure we're still in user's directory
            if not os.path.commonpath([full_path, user_dir]) == user_dir:
                flash('Access denied', 'error')
                return redirect(url_for('files.browse'))
        
        # Get directory contents
        items = []
        try:
            for item in os.scandir(full_path):
                try:
                    stat = item.stat()
                    items.append({
                        'name': item.name,
                        'filepath': os.path.join(current_dir, item.name) if current_dir else item.name,
                        'is_directory': item.is_dir(),
                        'size': stat.st_size,
                        'modified_at': datetime.fromtimestamp(stat.st_mtime),
                    })
                except (FileNotFoundError, PermissionError):
                    continue
        except (FileNotFoundError, PermissionError):
            flash('Directory not found or access denied', 'error')
            return redirect(url_for('files.browse'))
            
        # Sort items: directories first, then files, both alphabetically
        items.sort(key=lambda x: (not x['is_directory'], x['name'].lower()))
        
        # Get storage info
        storage_info = get_storage_info()
        
        return render_template('files/browse.html',
                           items=items,
                           current_dir=current_dir,
                           parent_dir=parent_dir,
                           **storage_info)
                           
    except Exception as e:
        current_app.logger.error(f"Error browsing files: {str(e)}")
        flash('Error accessing files', 'error')
        # Include storage info even in error case
        return render_template('files/browse.html', 
                             items=[], 
                             error=str(e),
                             **get_storage_info())
