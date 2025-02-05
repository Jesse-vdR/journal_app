from flask import Blueprint
import os

bp = Blueprint('scripts', __name__, url_prefix='/scripts')

# Ensure the scripts directory exists
def init_app(app):
    scripts_dir = os.path.join(app.root_path, 'scripts', 'available_scripts')
    os.makedirs(scripts_dir, exist_ok=True)

from app.scripts import routes
