from flask import Blueprint

superadmin_bp = Blueprint('superadmin', __name__)

from blueprints.superadmin import routes
