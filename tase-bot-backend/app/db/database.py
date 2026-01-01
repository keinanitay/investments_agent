import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

if not MONGO_URI or not DB_NAME:
    raise ValueError("MONGO_URI and DB_NAME must be set in .env file")

# configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()

async def connect_to_mongo():
    """initializes the mongodb connection using motor client."""
    db.client = AsyncIOMotorClient(MONGO_URI)
    db.db = db.client[DB_NAME]
    logger.info("Connected to MongoDB")

async def close_mongo_connection():
    """closes the mongodb connection."""
    db.client.close()
    logger.info("Closed MongoDB connection")

async def get_database():
    """returns the database instance."""
    return db.db