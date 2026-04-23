"""
Helper functions for MongoDB operations in ETL process
"""

import logging
from datetime import datetime, date
from typing import Dict, Any, Optional, Tuple
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)


def truncate_collection(collection: Collection):
    """
    Delete all documents from a collection (equivalent to TRUNCATE in SQL)
    """
    result = collection.delete_many({})
    logger.info(f"Truncated collection {collection.name}: {result.deleted_count} documents deleted")


def upsert_document(
    collection: Collection,
    filter_dict: Dict[str, Any],
    document: Dict[str, Any],
    add_updated_at: bool = True
) -> Tuple[bool, bool]:
    """
    Insert or update a document in MongoDB
    Returns: (was_inserted, was_updated) - True if inserted, False if updated
    """
    if add_updated_at:
        document['updated_at'] = datetime.utcnow()
    
    result = collection.update_one(
        filter_dict,
        {'$set': document},
        upsert=True
    )
    
    if result.upserted_id:
        return (True, False)  # Inserted
    else:
        return (False, True)  # Updated


def find_document(collection: Collection, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Find a single document in MongoDB
    """
    return collection.find_one(filter_dict)


def convert_date_to_string(d: Optional[date]) -> Optional[str]:
    """
    Convert date object to ISO string for MongoDB storage
    """
    if d is None:
        return None
    return d.isoformat()


def convert_string_to_date(s: Optional[str]) -> Optional[date]:
    """
    Convert ISO string to date object
    """
    if s is None:
        return None
    try:
        from datetime import datetime
        return datetime.fromisoformat(s).date()
    except:
        return None


def safe_float(value: Any) -> Optional[float]:
    """Safe conversion to float"""
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_int(value: Any) -> Optional[int]:
    """Safe conversion to int"""
    if value is None or value == '':
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def parse_date(date_string: Optional[str]) -> Optional[date]:
    """Parse date string to date object"""
    if not date_string:
        return None
    try:
        from datetime import datetime
        # Handle ISO format with or without timezone
        if 'Z' in date_string or '+' in date_string:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00')).date()
        else:
            return datetime.fromisoformat(date_string).date()
    except:
        return None

