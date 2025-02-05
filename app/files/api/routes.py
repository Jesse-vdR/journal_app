from flask import request, current_app, send_file, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import shutil

from app import db
from app.files.api import bp
from app.models import FileMetadata
from app.files.utils.path_utils import normalize_path, get_user_base_dir, get_safe_path

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['FILE_BROWSER_ALLOWED_EXTENSIONS']

@bp.route('/list', methods=['GET'])
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

@bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if file:
        filename = secure_filename(file.filename)
        extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if extension not in current_app.config['FILE_BROWSER_ALLOWED_EXTENSIONS']:
            allowed_ext = sorted(current_app.config['FILE_BROWSER_ALLOWED_EXTENSIONS'])
            return jsonify({
                'error': 'File type not allowed',
                'details': {
                    'extension': extension,
                    'allowed_extensions': allowed_ext
                }
            }), 400
            
        # Get user's home directory and current directory
        user_dir = current_user.get_home_directory()
        current_dir = request.form.get('current_dir', '').strip('/')
        
        # Create the full path for the file
        if current_dir:
            target_dir = os.path.join(user_dir, current_dir)
            file_path = os.path.join(target_dir, filename)
        else:
            file_path = os.path.join(user_dir, filename)
            
        # Security check - make sure we're still in user's directory
        if not os.path.commonpath([file_path, user_dir]) == user_dir:
            return jsonify({'error': 'Access denied'}), 403
            
        # Calculate file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        # Check if user has enough storage
        if not current_user.has_storage_space(file_size):
            return jsonify({
                'error': 'Storage limit exceeded',
                'details': {
                    'file_size_mb': round(file_size / (1024 * 1024), 2),
                    'storage_used_mb': round(current_user.storage_used / (1024 * 1024), 2),
                    'storage_limit_mb': round(current_user.storage_limit / (1024 * 1024), 2),
                    'storage_remaining_mb': round((current_user.storage_limit - current_user.storage_used) / (1024 * 1024), 2)
                }
            }), 400
            
        try:
            # Create target directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save the file
            file.save(file_path)
            
            # Update user's storage usage
            current_user.storage_used += file_size
            db.session.commit()
            
            return jsonify({
                'message': 'File uploaded successfully',
                'storage_used_mb': round(current_user.storage_used / (1024 * 1024), 2),
                'storage_remaining_mb': round((current_user.storage_limit - current_user.storage_used) / (1024 * 1024), 2)
            })
            
        except Exception as e:
            current_app.logger.error(f"Error uploading file: {str(e)}")
            return jsonify({'error': 'Error uploading file'}), 500
            
    return jsonify({'error': 'Invalid file'}), 400

@bp.route('/delete', methods=['POST'])
@login_required
def delete_item():
    try:
        path = request.form.get('path', '')
        if not path:
            return jsonify({'error': 'No path provided'}), 400
            
        base_dir = get_user_base_dir()
        abs_path = get_safe_path(base_dir, path)
        
        if not abs_path or not abs_path.startswith(base_dir):
            return jsonify({'error': 'Invalid path'}), 400
            
        if not os.path.exists(abs_path):
            return jsonify({'error': 'File not found'}), 404
            
        # Get file size before deletion
        file_size = os.path.getsize(abs_path) if os.path.isfile(abs_path) else 0
        
        # Delete the file or directory
        if os.path.isdir(abs_path):
            file_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                          for dirpath, dirnames, filenames in os.walk(abs_path)
                          for filename in filenames)
            os.rmdir(abs_path) if not os.listdir(abs_path) else shutil.rmtree(abs_path)
        else:
            os.remove(abs_path)
            
        # Update user's storage usage
        current_user.storage_used = max(0, current_user.storage_used - file_size)
        db.session.commit()
        
        metadata = FileMetadata.query.filter_by(
            filepath=path,
            owner_id=current_user.id
        ).first()
        if metadata:
            db.session.delete(metadata)
            db.session.commit()
            
        return jsonify({
            'message': 'File deleted successfully',
            'storage_used_mb': current_user.get_storage_used_mb(),
            'storage_remaining_mb': current_user.get_storage_remaining_mb()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error deleting file: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def get_directory_size(path):
    """Calculate total size of a directory"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total_size += os.path.getsize(fp)
            except (FileNotFoundError, PermissionError):
                continue
    return total_size

@bp.route('/delete/<path:path>', methods=['DELETE'])
@login_required
def delete_file(path):
    try:
        # Get user's home directory
        user_dir = current_user.get_home_directory()
        
        # Clean up path
        path = path.strip('/')
        file_path = os.path.join(user_dir, path)
        
        # Security check - make sure we're still in user's directory
        if not os.path.commonpath([file_path, user_dir]) == user_dir:
            return jsonify({'error': 'Access denied'}), 403
            
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
            
        # Calculate size before deleting
        if os.path.isdir(file_path):
            size_to_remove = get_directory_size(file_path)
            shutil.rmtree(file_path)  # Recursively remove directory
        else:
            size_to_remove = os.path.getsize(file_path)
            os.remove(file_path)  # Remove single file
        
        # Update user's storage usage
        current_user.storage_used = max(0, current_user.storage_used - size_to_remove)
        db.session.commit()
        
        return jsonify({'message': 'Item deleted successfully'})
        
    except Exception as e:
        current_app.logger.error(f"Error deleting item: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Error deleting item'}), 500

@bp.route('/download/<path:path>')
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

@bp.route('/create_folder', methods=['POST'])
@login_required
def create_folder():
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Folder name is required'}), 400

        folder_name = secure_filename(data['name'])
        if not folder_name:
            return jsonify({'error': 'Invalid folder name'}), 400

        # Get user's home directory
        user_dir = current_user.get_home_directory()
        
        # Get the current path (if any)
        current_path = data.get('path', '').strip('/')
        
        # Create the full path for the new folder
        if current_path:
            new_folder_path = os.path.join(user_dir, current_path, folder_name)
        else:
            new_folder_path = os.path.join(user_dir, folder_name)
            
        # Security check - make sure we're still in user's directory
        if not os.path.commonpath([new_folder_path, user_dir]) == user_dir:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if folder already exists
        if os.path.exists(new_folder_path):
            return jsonify({'error': 'A folder with this name already exists'}), 400
            
        # Create the folder
        os.makedirs(new_folder_path)
        
        return jsonify({'message': 'Folder created successfully'})
        
    except Exception as e:
        current_app.logger.error(f"Error creating folder: {str(e)}")
        return jsonify({'error': 'Error creating folder'}), 500
