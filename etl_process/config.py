import os
from dotenv import load_dotenv

load_dotenv()

# API configuration - try multiple env var names for compatibility
API_BASE_URL = os.getenv('API_BASE_URL') or os.getenv('TASE_API_BASE_URL') or os.getenv('SECURITIES_BASIC_API_URL')
API_KEY = os.getenv('API_KEY') or os.getenv('TASE_API_KEY') or os.getenv('SECURITIES_BASIC_API_KEY')

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

if not MONGO_URI or not DB_NAME:
    raise ValueError("MONGO_URI and DB_NAME must be set in .env file")

if not API_BASE_URL:
    raise ValueError("API_BASE_URL (or TASE_API_BASE_URL or SECURITIES_BASIC_API_URL) must be set in .env file")

if not API_KEY:
    raise ValueError("API_KEY (or TASE_API_KEY or SECURITIES_BASIC_API_KEY) must be set in .env file")