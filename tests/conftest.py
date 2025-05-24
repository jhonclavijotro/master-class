import pytest
from sap_middleware.app import app as flask_app # Import the Flask app instance
from sap_middleware.config import settings # Import the settings object

@pytest.fixture
def client():
    """
    Pytest fixture to create and configure a Flask test client.
    Sets TESTING mode and a specific API_KEY for test sessions.
    """
    # Configure the app for testing
    flask_app.config['TESTING'] = True
    
    # Override API_KEY for testing purposes
    # This ensures tests don't rely on a .env file or actual production keys
    original_api_key = settings.API_KEY
    settings.API_KEY = "test_api_key_for_testing" # Set a known key for tests
    
    # Create a test client using the Flask application context
    with flask_app.test_client() as client:
        yield client # Provide the client to the tests
    
    # Teardown: Restore original API_KEY after tests if necessary
    # This is good practice if settings are manipulated and might affect other tests
    # or parts of the application if it were a long-running test session.
    # For simple pytest runs, this might be less critical as state is usually isolated.
    settings.API_KEY = original_api_key

# You could also have a fixture to set up the app context if needed for other types of tests:
# @pytest.fixture
# def app_context(client): # client fixture already creates app context implicitly for test_client
#     with client.application.app_context():
#         yield client.application
