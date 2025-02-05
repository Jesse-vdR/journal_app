from flask import render_template, Response, current_app, request
from flask_login import login_required
import queue
import time
from datetime import datetime
import logging
import json

from app.monitor import bp

# Create a queue to store log messages
log_queue = queue.Queue()

# Create a custom log handler that puts messages in our queue
class QueueHandler(logging.Handler):
    def emit(self, record):
        try:
            log_entry = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'message': self.format(record),
                'level': record.levelname,
                'type': 'log'
            }
            log_queue.put(json.dumps(log_entry))
        except Exception as e:
            print(f"Error in QueueHandler: {e}")

def log_request():
    """Log details about the current request"""
    entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'message': f'{request.remote_addr} - "{request.method} {request.full_path}" {request.environ.get("SERVER_PROTOCOL", "")}',
        'level': 'INFO',
        'type': 'request'
    }
    log_queue.put(json.dumps(entry))

# Initialize handler with a more detailed format
handler = QueueHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

def init_app(app):
    """Initialize the monitoring with the Flask app"""
    # Add handler to Flask's logger
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    
    # Add handler to Werkzeug's logger
    logging.getLogger('werkzeug').addHandler(handler)
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    
    # Log all requests
    app.before_request(log_request)
    
    # Log startup message
    app.logger.info('Application started')

@bp.route('/')
@login_required
def index():
    """Show the monitoring dashboard"""
    return render_template('monitor/index.html')

@bp.route('/stream')
@login_required
def stream():
    """Stream logs using server-sent events"""
    def generate():
        while True:
            try:
                # Try to get a log message from the queue, timeout after 1 second
                log_entry = log_queue.get(timeout=1)
                yield f"data: {log_entry}\n\n"
            except queue.Empty:
                # If no new logs, send a heartbeat
                heartbeat = {
                    'type': 'heartbeat',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                yield f"data: {json.dumps(heartbeat)}\n\n"
            time.sleep(0.1)  # Small delay to prevent busy-waiting

    return Response(generate(), mimetype='text/event-stream')
