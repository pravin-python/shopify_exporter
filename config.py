import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-key')
    
    # Define base directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Instance folder path (where SQLite will be stored)
    INSTANCE_PATH = os.path.join(BASE_DIR, 'instance')
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
        'sqlite:///' + os.path.join(INSTANCE_PATH, 'shopify.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Shopify Configuration
    SHOPIFY_STORE = os.environ.get('SHOPIFY_STORE')
    SHOPIFY_ACCESS_TOKEN = os.environ.get('SHOPIFY_ACCESS_TOKEN')
    SHOPIFY_API_KEY = os.environ.get('SHOPIFY_API_KEY')
    SHOPIFY_API_SECRET = os.environ.get('SHOPIFY_API_SECRET')
    
    # USPS Configuration
    USPS_USER_ID = os.environ.get('USPS_USER_ID')
    
    # Ensure instance folder exists
    os.makedirs(INSTANCE_PATH, exist_ok=True)
