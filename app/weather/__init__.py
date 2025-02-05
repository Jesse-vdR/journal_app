from flask import Blueprint

bp = Blueprint('weather', __name__, url_prefix='/weather')

from app.weather import routes
