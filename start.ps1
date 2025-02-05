# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Set environment variables
$env:FLASK_APP = "run_server.py"
$env:FLASK_ENV = "development"

# Run the Flask application
python run_server.py

# The script will keep running until you press Ctrl+C
# When you do, it will deactivate the virtual environment automatically
