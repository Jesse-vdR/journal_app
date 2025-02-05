import sys
import logging
from datetime import datetime
from app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('flask.log')
    ]
)

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Add a startup message
    print("=" * 80)
    print(f"Starting Flask development server at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("WARNING: This is a development server. Do not use it in a production deployment.")
    print("Use a production WSGI server instead.")
    print("-" * 80)
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
    )
