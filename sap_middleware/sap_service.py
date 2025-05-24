import logging
from .config import settings

# Get a logger for this module
logger = logging.getLogger(__name__)

# Custom Exceptions
class SAPConnectionError(Exception):
    """Custom exception for SAP connection errors."""
    pass

class SAPNotFoundError(Exception):
    """Custom exception for when a resource is not found in SAP."""
    pass

class SAPOperationError(Exception):
    """Custom exception for errors during SAP operations."""
    pass

def connect_to_sap():
    """
    Simulates connecting to SAP using credentials from settings.
    Returns a dummy connection object or raises SAPConnectionError.
    """
    logger.info(f"Attempting to connect to SAP at {settings.SAP_HOST} with user {settings.SAP_USER} (simulated).")
    # Simulate connection success/failure
    if settings.SAP_HOST == "fail_connection": # Example condition for failure
        logger.error("SAP Connection Failed: Host unreachable (simulated)")
        raise SAPConnectionError("Failed to connect to SAP: Host unreachable (simulated)")
    
    logger.info("Successfully connected to SAP (simulated).")
    return {"status": "connected", "host": settings.SAP_HOST}

def read_material_data(material_id: str):
    """
    Simulates fetching material data from SAP for a given material_id.
    Returns a dictionary with sample material data or raises SAPNotFoundError.
    """
    logger.info(f"Attempting to fetch material data for '{material_id}' from SAP (simulated).")
    
    # Simulate a connection attempt for each operation for now
    # In a real app, connection might be managed differently (e.g., pooled)
    try:
        conn = connect_to_sap() # This function already logs its attempt and outcome
        if not conn: 
             # This case should ideally not be reached if connect_to_sap raises on failure
             logger.error("SAP connection object not returned from connect_to_sap for read_material_data.")
             raise SAPConnectionError("Connection not established for read_material_data (unexpected internal state)")
    except SAPConnectionError as e:
        logger.error(f"SAP Connection Error during read_material_data for '{material_id}': {e}")
        raise # Re-raise for the API layer to handle

    if material_id == "INVALID" or material_id == "NOT_FOUND":
        logger.warning(f"Material ID '{material_id}' not found in SAP (simulated).")
        raise SAPNotFoundError(f"Material with ID '{material_id}' not found.")
    
    if material_id == "ERROR_READ":
        logger.error(f"Simulating an error while reading material ID '{material_id}'.")
        raise SAPOperationError(f"Failed to read data for material '{material_id}' (simulated).")

    logger.info(f"Successfully fetched data for material '{material_id}' (simulated).")
    return {
        "material_id": material_id,
        "description": f"Sample Material {material_id}",
        "quantity": 100,
        "unit": "EA",
        "plant": "1000" 
    }

def create_sales_order(order_data: dict):
    """
    Simulates creating a sales order in SAP with the given order_data.
    Returns a dictionary with a success message and a dummy order ID,
    or raises SAPOperationError for issues.
    """
    # Be careful logging entire order_data in production if it contains sensitive info.
    # For this stub, logging keys or a summary might be okay.
    logger.info(f"Attempting to create sales order in SAP with data keys: {list(order_data.keys())} (simulated).")

    # Simulate a connection attempt
    try:
        conn = connect_to_sap() # This function already logs its attempt and outcome
        if not conn:
            # This case should ideally not be reached if connect_to_sap raises on failure
            logger.error("SAP connection object not returned from connect_to_sap for create_sales_order.")
            raise SAPConnectionError("Connection not established for create_sales_order (unexpected internal state)")
    except SAPConnectionError as e:
        logger.error(f"SAP Connection Error during create_sales_order: {e}")
        raise # Re-raise for the API layer to handle

    customer_id = order_data.get("customer_id")
    items = order_data.get("items")

    if not customer_id or not items:
        logger.warning(f"Sales order creation failed: Missing customer_id or items (simulated). Data provided: customer_id='{customer_id}', items_present={'yes' if items else 'no'}")
        raise SAPOperationError("Invalid order data: customer_id and items are required.")

    if customer_id == "FAIL_CUSTOMER":
        logger.warning(f"Sales order creation failed: Customer '{customer_id}' blocked or invalid (simulated).")
        raise SAPOperationError(f"Customer '{customer_id}' is not valid for sales order creation.")

    # Simulate order creation
    simulated_order_id = f"SO{abs(hash(str(order_data))) % 100000:05d}" # Generate a somewhat unique ID
    
    logger.info(f"Sales order '{simulated_order_id}' created successfully in SAP (simulated).")
    return {
        "status": "success",
        "order_id": simulated_order_id,
        "message": "Sales order created successfully in SAP (simulated)."
    }

# Example usage (optional, for testing this module directly)
if __name__ == '__main__':
    # Basic logging setup for direct script execution
    # This will print to console. In a real app, this logger would inherit app's config.
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("--- Testing SAP Service Module (Direct Execution) ---")
    
    # Test connection
    logger.info("\n1. Testing Connection:")
    try:
        connection = connect_to_sap()
        logger.info(f"Connection object: {connection}")
    except SAPConnectionError as e:
        logger.error(f"Connection Error: {e}")

    # Test with settings that cause connection failure
    logger.info("\n1b. Testing Connection Failure:")
    original_host = settings.SAP_HOST
    settings.SAP_HOST = "fail_connection" # Simulate a condition for failure
    try:
        connection = connect_to_sap()
        logger.info(f"Connection object: {connection}")
    except SAPConnectionError as e:
        logger.error(f"Connection Error: {e}")
    finally:
        settings.SAP_HOST = original_host # Reset for other tests
    
    # Test reading material data
    logger.info("\n2. Testing Read Material Data (Success):")
    try:
        material = read_material_data("MAT001")
        logger.info(f"Material Data: {material}")
    except (SAPConnectionError, SAPNotFoundError, SAPOperationError) as e:
        logger.error(f"Error reading material: {e}")

    logger.info("\n3. Testing Read Material Data (Not Found):")
    try:
        material = read_material_data("INVALID")
        logger.info(f"Material Data: {material}")
    except (SAPConnectionError, SAPNotFoundError, SAPOperationError) as e:
        logger.error(f"Error reading material: {e}")

    logger.info("\n4. Testing Read Material Data (Read Error):")
    try:
        material = read_material_data("ERROR_READ")
        logger.info(f"Material Data: {material}")
    except (SAPConnectionError, SAPNotFoundError, SAPOperationError) as e:
        logger.error(f"Error reading material: {e}")

    # Test creating sales order
    logger.info("\n5. Testing Create Sales Order (Success):")
    sample_order_success = {
        "customer_id": "CUST100",
        "items": [
            {"material_id": "MAT001", "quantity": 2},
            {"material_id": "MAT002", "quantity": 5}
        ],
        "document_type": "OR"
    }
    try:
        order_confirmation = create_sales_order(sample_order_success)
        logger.info(f"Order Confirmation: {order_confirmation}")
    except (SAPConnectionError, SAPOperationError) as e:
        logger.error(f"Error creating sales order: {e}")

    logger.info("\n6. Testing Create Sales Order (Invalid Data):")
    sample_order_fail_data = {
        "customer_id": "CUST200" 
        # Missing items
    }
    try:
        order_confirmation = create_sales_order(sample_order_fail_data)
        logger.info(f"Order Confirmation: {order_confirmation}")
    except (SAPConnectionError, SAPOperationError) as e:
        logger.error(f"Error creating sales order: {e}")

    logger.info("\n7. Testing Create Sales Order (Customer Blocked):")
    sample_order_fail_customer = {
        "customer_id": "FAIL_CUSTOMER",
        "items": [{"material_id": "MAT003", "quantity": 1}]
    }
    try:
        order_confirmation = create_sales_order(sample_order_fail_customer)
        logger.info(f"Order Confirmation: {order_confirmation}")
    except (SAPConnectionError, SAPOperationError) as e:
        logger.error(f"Error creating sales order: {e}")

    logger.info("\n--- End of SAP Service Module Tests (Direct Execution) ---")
