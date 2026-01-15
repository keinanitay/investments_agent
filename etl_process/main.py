"""
Test MongoDB connection
"""

import os
from dotenv import load_dotenv
from database import get_database, close_connection

load_dotenv()

# Test MongoDB connection
try:
    db = get_database()
    # Test connection by listing collections
    collections = db.list_collection_names()
    print(f"Connected to MongoDB database: {db.name}")
    print(f"Collections: {collections}")
    close_connection()
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    close_connection()
