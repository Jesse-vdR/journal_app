import os
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import render_template, jsonify, request, current_app, abort, send_file
from flask_login import login_required
from app.files import bp

def is_safe_path(path: str, base_dir: str) -> bool:
    """Check if the path is safe (within base directory)"""
    try:
        # Convert path to absolute and resolve any symlinks
        abs_path = os.path.abspath(os.path.join(base_dir, path.lstrip('/')))
        abs_base = os.path.abspath(base_dir)
        
        # Check if the path is within the base directory
        common_prefix = os.path.commonprefix([abs_path, abs_base])
        return common_prefix == abs_base
    except (TypeError, ValueError):
        return False

def get_absolute_path(path: str, base_dir: str) -> str:
    """Convert relative path to absolute path within base directory"""
    # Handle root path specially
    if path == '/' or not path:
        return base_dir
    
    # Remove leading slash and join with base directory
    return os.path.join(base_dir, path.lstrip('/'))

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config.get('FILE_BROWSER_ALLOWED_EXTENSIONS', set())

@bp.route('/browse')
@login_required
def browse():
    """Render the file browser page"""
    return render_template('files/browse.html')

@bp.route('/api/files')
@login_required
def list_files():
    """API endpoint to list files and directories"""
    base_dir = current_app.config.get('FILE_BROWSER_ROOT')
    if not base_dir:
        abort(500, description="FILE_BROWSER_ROOT not configured")
    
    path = request.args.get('path', '/')
    abs_path = get_absolute_path(path, base_dir)
    
    if not is_safe_path(path, base_dir):
        abort(403)  # Forbidden
    
    try:
        path_obj = Path(abs_path)
        if not path_obj.exists():
            abort(404)  # Not found
            
        items = []
        for item in path_obj.iterdir():
            try:
                is_dir = item.is_dir()
                rel_path = os.path.relpath(str(item), base_dir)
                item_info = {
                    'name': item.name,
                    'path': rel_path,
                    'type': 'directory' if is_dir else 'file',
                    'size': '' if is_dir else str(item.stat().st_size),
                    'modified': item.stat().st_mtime
                }
                items.append(item_info)
            except (PermissionError, OSError):
                continue
                
        # Sort items: directories first, then files, both alphabetically
        items.sort(key=lambda x: (x['type'] != 'directory', x['name'].lower()))
        
        # Get relative parent path
        parent_path = None
        if abs_path != base_dir:
            parent_path = os.path.relpath(str(path_obj.parent), base_dir)
            if parent_path == '.':
                parent_path = '/'
        
        return jsonify({
            'current_path': os.path.relpath(abs_path, base_dir) if abs_path != base_dir else '/',
            'parent_path': parent_path,
            'items': items
        })
        
    except Exception as e:
        current_app.logger.error(f"Error listing files: {str(e)}")
        abort(500)  # Internal server error

@bp.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Get the target directory from the form or use root
    base_dir = current_app.config.get('FILE_BROWSER_ROOT')
    if not base_dir:
        return jsonify({'error': 'FILE_BROWSER_ROOT not configured'}), 500
    
    path = request.form.get('path', '/')
    target_dir = get_absolute_path(path, base_dir)
    
    if not is_safe_path(path, base_dir):
        return jsonify({'error': 'Invalid target directory'}), 403
        
    try:
        # Create target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)
            
        # Secure the filename and create full path
        filename = secure_filename(file.filename)
        target_path = os.path.join(target_dir, filename)
        
        # Save the file
        file.save(target_path)
        
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename,
            'path': os.path.relpath(target_path, base_dir)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error uploading file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/download')
@login_required
def download_file():
    """Handle file download"""
    path = request.args.get('path')
    if not path:
        abort(400)  # Bad request
        
    base_dir = current_app.config.get('FILE_BROWSER_ROOT')
    if not base_dir:
        abort(500, description="FILE_BROWSER_ROOT not configured")
    
    abs_path = get_absolute_path(path, base_dir)
    if not is_safe_path(path, base_dir):
        abort(403)  # Forbidden
        
    try:
        return send_file(abs_path, as_attachment=True)
    except Exception as e:
        current_app.logger.error(f"Error downloading file: {str(e)}")
        abort(404)  # Not found
