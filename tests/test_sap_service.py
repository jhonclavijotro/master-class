import pytest
from sap_middleware import sap_service
from sap_middleware.sap_service import SAPNotFoundError, SAPConnectionError, SAPOperationError
from sap_middleware.config import settings

# To run tests:
# 1. Ensure you are in the project root directory.
# 2. Make sure pytest is installed (pip install pytest).
# 3. Run the command: python -m pytest
#    Alternatively: pytest

# These tests directly call the service layer functions.
# They rely on the simulated behavior defined in sap_service.py.

def test_connect_to_sap_success():
    """Test successful SAP connection simulation."""
    # Ensure no specific host setting that causes failure is active
    original_host = settings.SAP_HOST
    if settings.SAP_HOST == "fail_connection":
        settings.SAP_HOST = "test_host_success" # Temporarily set to a non-failing host
    
    connection = sap_service.connect_to_sap()
    assert connection is not None
    assert connection["status"] == "connected"
    
    if settings.SAP_HOST == "test_host_success": # Clean up if we changed it
        settings.SAP_HOST = original_host

def test_connect_to_sap_failure():
    """Test simulated SAP connection failure."""
    original_host = settings.SAP_HOST
    settings.SAP_HOST = "fail_connection" # This special value triggers failure in the stub
    
    with pytest.raises(SAPConnectionError) as excinfo:
        sap_service.connect_to_sap()
    assert "Failed to connect to SAP: Host unreachable (simulated)" in str(excinfo.value)
    
    settings.SAP_HOST = original_host # Restore original host

def test_read_material_data_success():
    """Test successful material data retrieval."""
    material = sap_service.read_material_data("MAT001")
    assert material is not None
    assert material["material_id"] == "MAT001"
    assert "description" in material

def test_read_material_data_not_found():
    """Test SAPNotFoundError for an invalid material ID."""
    with pytest.raises(SAPNotFoundError) as excinfo:
        sap_service.read_material_data("INVALID") # INVALID triggers SAPNotFoundError in stub
    assert "Material with ID 'INVALID' not found" in str(excinfo.value)

def test_read_material_data_operation_error():
    """Test SAPOperationError during material read."""
    with pytest.raises(SAPOperationError) as excinfo:
        sap_service.read_material_data("ERROR_READ") # ERROR_READ triggers SAPOperationError
    assert "Failed to read data for material 'ERROR_READ' (simulated)" in str(excinfo.value)

def test_read_material_data_connection_error():
    """Test connection error during material read."""
    original_host = settings.SAP_HOST
    settings.SAP_HOST = "fail_connection"
    
    with pytest.raises(SAPConnectionError):
        sap_service.read_material_data("ANY_MAT_ID")
        
    settings.SAP_HOST = original_host

def test_create_sales_order_success():
    """Test successful sales order creation."""
    order_data = {
        "customer_id": "CUST123",
        "items": [{"material_id": "MATXYZ", "quantity": 10}],
        "details": {"notes": "Service layer test order"} # Added details for consistency if it was checked
    }
    confirmation = sap_service.create_sales_order(order_data)
    assert confirmation is not None
    assert confirmation["status"] == "success"
    assert "order_id" in confirmation

def test_create_sales_order_missing_data():
    """Test SAPOperationError for missing customer_id or items in sales order."""
    order_data_no_items = {
        "customer_id": "CUST456",
        "details": {}
        # "items" key is missing
    }
    with pytest.raises(SAPOperationError) as excinfo:
        sap_service.create_sales_order(order_data_no_items)
    assert "Invalid order data: customer_id and items are required" in str(excinfo.value)

    order_data_no_customer = {
        "items": [{"material_id": "MAT789", "quantity": 5}],
        "details": {}
        # "customer_id" is missing
    }
    with pytest.raises(SAPOperationError) as excinfo:
        sap_service.create_sales_order(order_data_no_customer)
    assert "Invalid order data: customer_id and items are required" in str(excinfo.value)

def test_create_sales_order_fail_customer():
    """Test SAPOperationError for a 'FAIL_CUSTOMER'."""
    order_data = {
        "customer_id": "FAIL_CUSTOMER", # This triggers specific error in stub
        "items": [{"material_id": "MATFC", "quantity": 1}],
        "details": {}
    }
    with pytest.raises(SAPOperationError) as excinfo:
        sap_service.create_sales_order(order_data)
    assert "Customer 'FAIL_CUSTOMER' is not valid for sales order creation" in str(excinfo.value)

def test_create_sales_order_connection_error():
    """Test connection error during sales order creation."""
    original_host = settings.SAP_HOST
    settings.SAP_HOST = "fail_connection"
    
    order_data = {
        "customer_id": "CUST789",
        "items": [{"material_id": "MATABC", "quantity": 3}],
        "details": {}
    }
    with pytest.raises(SAPConnectionError):
        sap_service.create_sales_order(order_data)
        
    settings.SAP_HOST = original_host
