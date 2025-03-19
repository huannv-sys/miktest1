from flask import Blueprint

bp = Blueprint('main', __name__)

from mik.app.main import routes