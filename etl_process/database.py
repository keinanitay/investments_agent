"""
MongoDB database connection and utilities for ETL process
"""

import logging
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Optional
from config import MONGO_URI, DB_NAME

logger = logging.getLogger(__name__)

# Global MongoDB client
_client: Optional[MongoClient] = None
_db: Optional[Database] = None


def get_mongo_client() -> MongoClient:
    """Get or create MongoDB client"""
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
        logger.info("Connected to MongoDB")
    return _client


def get_database() -> Database:
    """Get database instance"""
    global _db
    if _db is None:
        client = get_mongo_client()
        _db = client[DB_NAME]
    return _db


def close_connection():
    """Close MongoDB connection"""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("Closed MongoDB connection")


def get_collection(collection_name: str) -> Collection:
    """Get a collection from the database"""
    db = get_database()
    return db[collection_name]

