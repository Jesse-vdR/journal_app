from flask import Blueprint

bp = Blueprint('monitor', __name__, url_prefix='/monitor')

from app.monitor import routes

def init_app(app):
    app.register_blueprint(bp)
    routes.init_app(app)
