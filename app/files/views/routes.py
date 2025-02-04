from flask import render_template, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
import os
from datetime import datetime

from app import db
from app.files import bp
from app.models import FileMetadata
from app.files.utils.path_utils import normalize_path, get_user_base_dir, get_safe_path

@bp.route('/browse/')
@bp.route('/browse/<path:path>')
@login_required
def browse_files(path=''):
    """Browse files in the user's directory"""
    base_dir = get_user_base_dir()
    abs_path = get_safe_path(base_dir, path)
    
    if not abs_path:
        flash('Invalid path', 'error')
        return redirect(url_for('files.browse_files'))
    
    parent_path = os.path.dirname(path) if path else None
    
    try:
        items = []
        for item_name in os.listdir(abs_path):
            item_path = os.path.join(abs_path, item_name)
            is_dir = os.path.isdir(item_path)
            rel_path = os.path.join(path, item_name).replace('\\', '/') if path else item_name
            
            item = {
                'filename': item_name,
                'filepath': rel_path,
                'is_directory': is_dir,
                'filesize': os.path.getsize(item_path) if not is_dir else 0,
                'modified_at': datetime.fromtimestamp(os.path.getmtime(item_path)),
                'file_type_icon': 'bi bi-folder' if is_dir else 'bi bi-file-earmark'
            }
            items.append(item)
            
        items.sort(key=lambda x: (not x['is_directory'], x['filename'].lower()))
        
    except Exception as e:
        current_app.logger.error(f"Error listing directory: {str(e)}")
        flash('Error accessing directory', 'error')
        db.session.rollback()
        return redirect(url_for('files.browse_files'))
    
    breadcrumbs = []
    if path:
        parts = path.split('/')
        current = ''
        for part in parts:
            if current:
                current = f"{current}/{part}"
            else:
                current = part
            breadcrumbs.append({
                'name': part,
                'path': current
            })
    
    return render_template('files/browse.html',
                         items=items,
                         current_path=path,
                         parent_path=parent_path,
                         breadcrumbs=breadcrumbs)
