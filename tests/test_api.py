import pytest
import json
from sap_middleware.config import settings # Used to get the test API key

# To run tests:
# 1. Ensure you are in the project root directory.
# 2. Make sure pytest is installed (pip install pytest).
# 3. Run the command: python -m pytest
#    Alternatively: pytest

# The client fixture is defined in conftest.py and handles app setup for testing.
# It also sets settings.API_KEY = "test_api_key_for_testing"

def test_get_material_success(client):
    """Test successful retrieval of material data."""
    headers = {'X-API-KEY': settings.API_KEY} # Use the key set in conftest
    response = client.get('/api/sap/material/TESTMAT', headers=headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['material_id'] == 'TESTMAT'
    assert 'description' in json_data

def test_get_material_not_found(client):
    """Test material not found (SAPNotFoundError)."""
    headers = {'X-API-KEY': settings.API_KEY}
    response = client.get('/api/sap/material/INVALID', headers=headers) # INVALID is a special ID for testing
    assert response.status_code == 404
    json_data = response.get_json()
    assert "Material with ID 'INVALID' not found" in json_data['error']

def test_get_material_no_api_key(client):
    """Test request without API key."""
    response = client.get('/api/sap/material/TESTMAT')
    assert response.status_code == 401
    json_data = response.get_json()
    assert "Invalid or missing API Key" in json_data['message']

def test_get_material_invalid_api_key(client):
    """Test request with an invalid API key."""
    headers = {'X-API-KEY': 'wrong_key'}
    response = client.get('/api/sap/material/TESTMAT', headers=headers)
    assert response.status_code == 401
    json_data = response.get_json()
    assert "Invalid or missing API Key" in json_data['message']

def test_create_sales_order_success(client):
    """Test successful creation of a sales order."""
    headers = {
        'X-API-KEY': settings.API_KEY,
        'Content-Type': 'application/json'
    }
    payload = {
        "customer_id": "CUST001",
        "items": [{"material_id": "MAT001", "quantity": 10}],
        "details": {"notes": "Test order"} # 'details' key is required by current app.py validation
    }
    response = client.post('/api/sap/sales_order', data=json.dumps(payload), headers=headers)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert 'order_id' in json_data

def test_create_sales_order_bad_request_missing_details(client):
    """Test sales order creation with invalid JSON payload (missing 'details')."""
    headers = {
        'X-API-KEY': settings.API_KEY,
        'Content-Type': 'application/json'
    }
    payload = { # Missing 'details' key
        "customer_id": "CUST002",
        "items": [{"material_id": "MAT002", "quantity": 5}]
    }
    response = client.post('/api/sap/sales_order', data=json.dumps(payload), headers=headers)
    assert response.status_code == 400 # As per app.py validation
    json_data = response.get_json()
    assert "Invalid input: 'details' key missing in JSON payload" in json_data['error']

def test_create_sales_order_bad_request_sap_operation_error(client):
    """Test sales order creation that causes SAPOperationError (e.g., missing customer_id)."""
    headers = {
        'X-API-KEY': settings.API_KEY,
        'Content-Type': 'application/json'
    }
    # sap_service.create_sales_order expects 'customer_id' and 'items'
    # and raises SAPOperationError if they are missing.
    payload = { 
        "details": {"notes": "Test order but missing core fields"}
        # "customer_id" is missing
    }
    response = client.post('/api/sap/sales_order', data=json.dumps(payload), headers=headers)
    # The app.py endpoint currently maps SAPOperationError to 400 for sales orders
    assert response.status_code == 400 
    json_data = response.get_json()
    assert "Invalid order data: customer_id and items are required" in json_data['error']


def test_create_sales_order_no_api_key(client):
    """Test sales order creation without API key."""
    headers = {'Content-Type': 'application/json'}
    payload = {
        "customer_id": "CUST003",
        "items": [{"material_id": "MAT003", "quantity": 2}],
        "details": {"notes": "Test order no key"}
    }
    response = client.post('/api/sap/sales_order', data=json.dumps(payload), headers=headers)
    assert response.status_code == 401
    json_data = response.get_json()
    assert "Invalid or missing API Key" in json_data['message']

def test_root_path_hello(client):
    """Test the root path to ensure it returns the hello message."""
    # This doesn't require API key as per current setup
    response = client.get('/')
    assert response.status_code == 200
    assert b"Hello, SAP Middleware!" in response.data

def test_global_not_found_error(client):
    """Test the global 404 error handler for an undefined route."""
    headers = {'X-API-KEY': settings.API_KEY} # Key needed if it were a protected base path
    response = client.get('/nonexistent/route', headers=headers)
    assert response.status_code == 404
    json_data = response.get_json()
    assert json_data['error'] == 'Not Found'
    assert "The requested URL was not found on the server" in json_data['message']

def test_global_method_not_allowed_error(client):
    """Test the global 405 error handler."""
    headers = {'X-API-KEY': settings.API_KEY}
    # Try to POST to a GET-only route (e.g., get_material)
    response = client.post('/api/sap/material/TESTMAT', headers=headers, data=json.dumps({}))
    assert response.status_code == 405
    json_data = response.get_json()
    assert json_data['error'] == 'Method Not Allowed'

# Further tests could include:
# - Testing SAPConnectionError (503) by mocking connect_to_sap to raise it.
#   This would require more advanced fixture/mocking setup.
#   Example: settings.SAP_HOST = "fail_connection" before the call.
# - Testing the generic 500 error by forcing an unhandled exception.
# - Testing logging output (more complex, might need to capture logs).
