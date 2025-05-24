from functools import wraps
from flask import request, jsonify
from .config import settings # Relative import for settings

def api_key_required(f):
    """
    Decorator to protect routes with API key authentication.
    Checks for 'X-API-KEY' header and validates against settings.API_KEY.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if api_key and api_key == settings.API_KEY:
            return f(*args, **kwargs)
        else:
            # Log the attempt for security auditing if needed
            # app.logger.warning(f"Unauthorized API access attempt. Missing/Invalid Key. IP: {request.remote_addr}")
            return jsonify({"message": "Unauthorized: Invalid or missing API Key"}), 401
    return decorated_function
