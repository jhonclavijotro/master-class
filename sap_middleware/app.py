import logging
from logging.handlers import RotatingFileHandler
import os
from flask import Flask, jsonify, request
from .config import settings
from . import sap_service
from .sap_service import SAPNotFoundError, SAPConnectionError, SAPOperationError
from .auth import api_key_required # Import the decorator

app = Flask(__name__)

# --- Logging Configuration ---
log_level = logging.DEBUG if settings.DEBUG else logging.INFO
log_format = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

# File Handler
# Ensure the 'instance' folder exists (Flask standard for non-committable instance data)
instance_path = os.path.join(app.root_path, '..', 'instance') # app.root_path is sap_middleware, so '..' gets to project root
if not os.path.exists(instance_path):
    os.makedirs(instance_path)
log_file = os.path.join(instance_path, 'sap_middleware.log')

file_handler = RotatingFileHandler(log_file, maxBytes=1024*1024*5, backupCount=2) # 5MB per file, 2 backups
file_handler.setFormatter(log_format)

# Stream Handler (Console)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_format)

# Configure app.logger (Flask's default logger)
# Remove default handlers if any, to avoid duplicate logs if FLASK_DEBUG is also setting up logging.
# However, Flask in production mode doesn't add handlers by default,
# and in debug mode, it adds a StreamHandler.
# For consistency, we'll manage handlers directly.
if not app.debug: # Or check settings.FLASK_ENV == 'production'
    # In production, add our handlers.
    # In debug mode, Flask's own handler might be sufficient for console,
    # but we add file handler for persistence.
    # Let's clear existing handlers to be sure and add ours.
    app.logger.handlers.clear()
    app.logger.addHandler(file_handler)
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(log_level)
else:
    # In debug mode, Flask adds a StreamHandler. We can add our file handler.
    # Or, like above, take full control. Let's take full control for consistency.
    app.logger.handlers.clear()
    app.logger.addHandler(file_handler)
    app.logger.addHandler(stream_handler) # Add stream handler too for debug console
    app.logger.setLevel(logging.DEBUG) # Always DEBUG if Flask debug is on

# Also configure the root logger if you want other libraries' logs (e.g. werkzeug)
# logging.basicConfig(level=log_level, format='%(asctime)s %(levelname)s %(message)s', handlers=[file_handler, stream_handler])
# For now, focusing on app.logger. If basicConfig was called before app.logger setup, it might conflict or be overridden.
# It's generally better to configure app.logger directly or use basicConfig very early and let Flask pick it up.
# For this task, directly managing app.logger.handlers is more explicit.

# Configuration is typically loaded when 'settings' is imported due to python-dotenv.
# Flask CLI (flask run) will use FLASK_APP, FLASK_ENV, DEBUG from .env.
# If running directly with `python app.py`, Flask's default debug mode might be used
# unless explicitly set from settings.
app.config['DEBUG'] = settings.DEBUG
app.config['ENV'] = settings.FLASK_ENV

# --- Global Error Handlers ---
@app.errorhandler(400)
def bad_request_error(error):
    app.logger.error(f"Bad Request (400): {error}")
    return jsonify({"error": "Bad Request", "message": str(error)}), 400

@app.errorhandler(401)
def unauthorized_error(error):
    # This might be triggered by werkzeug if a @login_required (from Flask-Login, not used here)
    # or similar auth mechanism fails before our @api_key_required decorator's direct response.
    # Our @api_key_required already returns a specific 401.
    app.logger.error(f"Unauthorized (401): {error}")
    return jsonify({"error": "Unauthorized", "message": str(error)}), 401

@app.errorhandler(404)
def not_found_error(error):
    app.logger.error(f"Not Found (404): {error}")
    return jsonify({"error": "Not Found", "message": "The requested URL was not found on the server."}), 404

@app.errorhandler(405)
def method_not_allowed_error(error):
    app.logger.error(f"Method Not Allowed (405): {error}")
    return jsonify({"error": "Method Not Allowed", "message": str(error)}), 405

@app.errorhandler(500)
def internal_server_error(error):
    app.logger.error(f"Internal Server Error (500): {error}")
    # Avoid leaking detailed internal error messages in production if str(error) is too verbose.
    # For the stub, str(error) is okay.
    return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred on the server."}), 500

# Catch-all for other werkzeug HTTPExceptions
# This might be redundant if specific ones are handled, but can be a fallback.
# from werkzeug.exceptions import HTTPException
# @app.errorhandler(HTTPException)
# def handle_http_exception(e):
#     """Return JSON instead of HTML for HTTP errors."""
#     app.logger.error(f"HTTP Exception ({e.code}): {e.name} - {e.description}")
#     response = e.get_response()
#     response.data = json.dumps({
#         "code": e.code,
#         "name": e.name,
#         "description": e.description,
#     })
#     response.content_type = "application/json"
#     return response

@app.route('/')
def hello():
    return "Hello, SAP Middleware!"

@app.route('/api/sap/material/<string:material_id>', methods=['GET'])
@api_key_required # Apply the decorator
def get_material(material_id):
    app.logger.info(f"Request received for GET /api/sap/material/{material_id}")
    # Log API key presence for audit, but not the key itself for security.
    # app.logger.debug(f"X-API-KEY header present: {'yes' if 'X-API-KEY' in request.headers else 'no'}")
    try:
        app.logger.info(f"Attempting to read material data for ID: {material_id}")
        material_data = sap_service.read_material_data(material_id)
        app.logger.info(f"Successfully fetched material data for ID: {material_id}")
        return jsonify(material_data), 200
        # The 'else' case for material_data not being found might not be hit
        # if sap_service always raises SAPNotFoundError as per current design.
    except SAPNotFoundError as e:
        app.logger.warning(f"Material ID '{material_id}' not found: {e}")
        return jsonify({"error": str(e)}), 404
    except SAPConnectionError as e:
        app.logger.error(f"SAP connection error for material ID '{material_id}': {e}")
        return jsonify({"error": f"SAP connection error: {str(e)}"}), 503
    except SAPOperationError as e:
        app.logger.error(f"SAP operation error for material ID '{material_id}': {e}")
        return jsonify({"error": f"SAP operation error: {str(e)}"}), 500
    except Exception as e:
        # Catch-all for other unexpected errors
        app.logger.error(f"Unexpected error fetching material {material_id}: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/api/sap/sales_order', methods=['POST'])
@api_key_required # Apply the decorator
def create_sales_order_api():
    app.logger.info("Request received for POST /api/sap/sales_order")
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            app.logger.warning("Invalid sales order input: No JSON data or not a dict.")
            return jsonify({"error": "Invalid input: JSON data expected"}), 400

        if 'details' not in data: # Simple check as per instruction
            app.logger.warning("Invalid sales order input: 'details' key missing.")
            return jsonify({"error": "Invalid input: 'details' key missing in JSON payload"}), 400
        
        app.logger.info("Attempting to create sales order.")
        # Sensitive data like order details should not be logged in full in production.
        # app.logger.debug(f"Sales order data (partial/keys): {list(data.keys())}") 
        order_confirmation = sap_service.create_sales_order(data)
        app.logger.info(f"Successfully created sales order, ID: {order_confirmation.get('order_id')}")
        
        return jsonify(order_confirmation), 201

    except SAPConnectionError as e:
        app.logger.error(f"SAP connection error during sales order creation: {e}")
        return jsonify({"error": f"SAP connection error: {str(e)}"}), 503
    except SAPOperationError as e:
        app.logger.error(f"SAP operation error during sales order creation: {e}")
        return jsonify({"error": f"SAP operation error: {str(e)}"}), 400 
    except Exception as e:
        app.logger.error(f"Unexpected error creating sales order: {e}") # This already existed and is good.
        return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    # When running with `python app.py`, use host/port from settings or defaults.
    # For production, a proper WSGI server like Gunicorn or uWSGI should be used.
    app.run(host=settings.FLASK_RUN_HOST or '0.0.0.0', 
            port=int(settings.FLASK_RUN_PORT or 5000), 
            debug=settings.DEBUG)
