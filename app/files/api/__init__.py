from flask import Blueprint

bp = Blueprint('files_api', __name__, url_prefix='/api/files')

from app.files.api import routes  # noqa
