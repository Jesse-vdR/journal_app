from flask import request, current_app, send_file, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename
from datetime import datetime

from app import db
from app.files import api_bp
from app.models import FileMetadata
from app.files.utils.path_utils import normalize_path, get_user_base_dir, get_safe_path

@api_bp.route('/list', methods=['GET'])
@login_required
def list_files():
    """List files in a directory"""
    path = normalize_path(request.args.get('path'))
    base_dir = get_user_base_dir()
    abs_path = get_safe_path(base_dir, path)
    
    if not abs_path:
        return {'error': 'Invalid path'}, 400
        
    try:
        items = []
        for item in os.listdir(abs_path):
            item_path = os.path.join(abs_path, item)
            is_dir = os.path.isdir(item_path)
            items.append({
                'name': item,
                'is_directory': is_dir,
                'size': os.path.getsize(item_path) if not is_dir else 0,
                'modified': datetime.fromtimestamp(os.path.getmtime(item_path)).isoformat()
            })
        return {'items': items}
    except Exception as e:
        current_app.logger.error(f"Error listing files: {str(e)}")
        return {'error': 'Error listing files'}, 500

@api_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return {'success': False, 'error': 'No file selected'}, 400
    
    file = request.files['file']
    if file.filename == '':
        return {'success': False, 'error': 'No file selected'}, 400
    
    path = normalize_path(request.form.get('path'))
    base_dir = get_user_base_dir()
    abs_path = get_safe_path(base_dir, path)
    
    if not abs_path:
        return {'success': False, 'error': 'Invalid path'}, 400
    
    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(abs_path, filename)
        file.save(file_path)
        
        rel_path = os.path.join(path, filename).replace('\\', '/') if path else filename
        metadata = FileMetadata(
            filename=filename,
            filepath=rel_path,
            owner_id=current_user.id
        )
        db.session.add(metadata)
        db.session.commit()
        
        return {'success': True, 'message': 'File uploaded successfully'}
    except Exception as e:
        current_app.logger.error(f"Error uploading file: {str(e)}")
        db.session.rollback()
        return {'success': False, 'error': 'Error uploading file'}, 500

@api_bp.route('/delete', methods=['POST'])
@login_required
def delete_item():
    """Delete a file or directory"""
    path = normalize_path(request.form.get('path'))
    base_dir = get_user_base_dir()
    abs_path = get_safe_path(base_dir, path)
    
    if not abs_path:
        return {'error': 'Invalid path'}, 400
    
    try:
        if os.path.isdir(abs_path):
            os.rmdir(abs_path)
        else:
            os.remove(abs_path)
            
        metadata = FileMetadata.query.filter_by(
            filepath=path,
            owner_id=current_user.id
        ).first()
        if metadata:
            db.session.delete(metadata)
            db.session.commit()
            
        return {'success': True}
    except Exception as e:
        current_app.logger.error(f"Error deleting file: {str(e)}")
        db.session.rollback()
        return {'error': str(e)}, 500

@api_bp.route('/download/<path:path>')
@login_required
def download_file(path):
    """Download a file"""
    path = normalize_path(path)
    base_dir = get_user_base_dir()
    abs_path = get_safe_path(base_dir, path)
    
    if not abs_path or not os.path.isfile(abs_path):
        flash('File not found', 'error')
        return redirect(url_for('files.browse_files'))
        
    try:
        return send_file(abs_path, as_attachment=True)
    except Exception as e:
        current_app.logger.error(f"Error downloading file: {str(e)}")
        flash('Error downloading file', 'error')
        return redirect(url_for('files.browse_files'))

@api_bp.route('/create_folder', methods=['POST'])
@login_required
def create_folder():
    """Create a new folder"""
    path = normalize_path(request.form.get('path'))
    name = request.form.get('name')
    
    if not name:
        return {'error': 'No folder name specified'}, 400
    
    base_dir = get_user_base_dir()
    parent_path = get_safe_path(base_dir, path)
    
    if not parent_path:
        return {'error': 'Invalid path'}, 400
    
    try:
        new_folder_path = os.path.join(parent_path, name)
        if os.path.exists(new_folder_path):
            return {'error': 'Folder already exists'}, 400
            
        os.makedirs(new_folder_path)
        return {'success': True}
    except Exception as e:
        current_app.logger.error(f"Error creating folder: {str(e)}")
        return {'error': str(e)}, 500
