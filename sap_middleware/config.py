import os
from dotenv import load_dotenv

# Load environment variables from .env file
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(basedir, '.env'))

class Settings:
    """
    Configuration class for the SAP Middleware application.
    Loads settings from environment variables.
    """
    # SAP Connection Details
    SAP_HOST = os.getenv('SAP_HOST')
    SAP_CLIENT = os.getenv('SAP_CLIENT')
    SAP_USER = os.getenv('SAP_USER')
    SAP_PASSWORD = os.getenv('SAP_PASSWORD')
    SAP_SYSTEM_NUMBER = os.getenv('SAP_SYSTEM_NUMBER')

    # API Key for Middleware
    API_KEY = os.getenv('API_KEY')

    # Flask Environment Settings (already used by Flask CLI but good to have)
    FLASK_APP = os.getenv('FLASK_APP', 'sap_middleware/app.py')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# Export an instance of the settings
settings = Settings()
