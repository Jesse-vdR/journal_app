from flask import Blueprint

bp = Blueprint('accounts', __name__, url_prefix='/accounts')

from app.accounts import routes
