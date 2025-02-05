from flask import render_template, jsonify, current_app
from flask_login import login_required
import os
import sys
import io
import importlib.util
import threading
import queue
import time
from datetime import datetime
import contextlib
import traceback

from app.scripts import bp

# Queue to store script output
output_queues = {}

class OutputCapture:
    def __init__(self):
        self.output = io.StringIO()
    
    def write(self, text):
        self.output.write(text)
        
    def flush(self):
        pass
    
    def getvalue(self):
        return self.output.getvalue()

def run_script_in_thread(script_name, queue_id, app):
    """Run a script in a separate thread and capture its output"""
    scripts_dir = None
    
    try:
        with app.app_context():
            # Create output capture
            output_capture = OutputCapture()
            
            # Get script directory
            scripts_dir = os.path.join(app.root_path, 'scripts', 'available_scripts')
            script_path = os.path.join(scripts_dir, f'{script_name}.py')
            
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"Script {script_name}.py not found")
            
            # Add scripts directory to Python path
            if scripts_dir not in sys.path:
                sys.path.insert(0, scripts_dir)
            
            # Redirect stdout and stderr
            with contextlib.redirect_stdout(output_capture), contextlib.redirect_stderr(output_capture):
                try:
                    # Import the script
                    spec = importlib.util.spec_from_file_location(script_name, script_path)
                    if spec is None:
                        raise ImportError(f"Could not load script {script_name}")
                        
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[script_name] = module
                    spec.loader.exec_module(module)
                    
                    # Run the script
                    if not hasattr(module, 'run'):
                        raise AttributeError(f"Script {script_name} has no run() function")
                        
                    success = module.run()
                    
                    # Get the output
                    output = output_capture.getvalue()
                    
                    # Put the output in the queue
                    output_queues[queue_id].put({
                        'status': 'complete',
                        'success': success,
                        'output': output,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                except Exception as e:
                    raise RuntimeError(f"Error executing script: {str(e)}")
                    
    except Exception as e:
        error_output = output_capture.getvalue() if 'output_capture' in locals() else ''
        error_message = f"Script error: {str(e)}\n{traceback.format_exc()}"
        
        with app.app_context():
            current_app.logger.error(error_message)
        
        output_queues[queue_id].put({
            'status': 'error',
            'error': error_message,
            'output': error_output if error_output else None,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    finally:
        # Remove script directory from Python path
        if scripts_dir and scripts_dir in sys.path:
            sys.path.remove(scripts_dir)
            
        # Clean up queue
        if queue_id in output_queues:
            del output_queues[queue_id]

@bp.route('/')
@login_required
def index():
    """Show available scripts"""
    scripts_dir = os.path.join(current_app.root_path, 'scripts', 'available_scripts')
    scripts = []
    
    for file in os.listdir(scripts_dir):
        if file.endswith('.py') and not file.startswith('__'):
            script_name = file[:-3]  # Remove .py extension
            
            # Import the script to get its docstring
            spec = importlib.util.spec_from_file_location(script_name, os.path.join(scripts_dir, file))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            scripts.append({
                'name': script_name,
                'description': module.run.__doc__ or 'No description available'
            })
    
    return render_template('scripts/index.html', scripts=scripts)

@bp.route('/run/<script_name>')
@login_required
def run_script(script_name):
    """Run a script and return a queue ID for getting its output"""
    queue_id = f"{script_name}_{int(time.time())}"
    output_queues[queue_id] = queue.Queue()
    
    # Start the script in a separate thread
    thread = threading.Thread(
        target=run_script_in_thread, 
        args=(script_name, queue_id, current_app._get_current_object())
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'queue_id': queue_id})

@bp.route('/output/<queue_id>')
@login_required
def get_output(queue_id):
    """Get the output from a running script"""
    if queue_id not in output_queues:
        return jsonify({'status': 'not_found'})
    
    try:
        # Try to get output from the queue
        output = output_queues[queue_id].get_nowait()
        
        # Format the output for display
        if 'output' in output and output['output']:
            # Split into lines and format each line
            lines = output['output'].splitlines()
            output['output'] = '\n'.join(lines)
        
        return jsonify(output)
    except queue.Empty:
        return jsonify({'status': 'running'})
