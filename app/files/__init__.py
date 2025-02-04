from flask import Blueprint

bp = Blueprint('files', __name__, url_prefix='/files')
api_bp = Blueprint('files_api', __name__, url_prefix='/files/api')

# Import routes from submodules
from app.files.api import routes as api_routes
from app.files.views import routes as view_routes

# Register blueprints
def init_app(app):
    app.register_blueprint(bp)
    app.register_blueprint(api_bp)
