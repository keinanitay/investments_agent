"""
Extract delisted securities list from TASE API
Saves data to MongoDB collections
"""

import logging
import requests
from datetime import date
from typing import Dict, List, Optional, Tuple

# Import MongoDB utilities
from config import API_BASE_URL, API_KEY
from database import get_collection
from mongo_helpers import (
    truncate_collection, upsert_document,
    parse_date, convert_date_to_string
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extract_delisted_securities_list.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API configuration
DELISTED_SECURITIES_LIST_ENDPOINT = f"{API_BASE_URL}/basic-securities/delisted-securities-list"

# MongoDB collection names
STG_COLLECTION = "stg_delisted_securities_list"
CORE_COLLECTION = "core_delisted_securities_list"


class DelistedSecuritiesListExtractor:
    """
    Extract delisted securities list from TASE API
    """
    
    def __init__(self):
        """Initialize extractor"""
        # Setup API session
        self.session = requests.Session()
        self.session.headers.update({
            'ApiKey': API_KEY,
            'Accept': 'application/json',
            'Accept-Language': 'he-IL'
        })
        
        # Get MongoDB collections
        self.stg_collection = get_collection(STG_COLLECTION)
        self.core_collection = get_collection(CORE_COLLECTION)
        
        # Create indexes
        self._create_indexes()
        
        logger.info("API: %s", API_BASE_URL)
        logger.info("Delisted Securities List: %s", DELISTED_SECURITIES_LIST_ENDPOINT)
        logger.info("Connected to API and MongoDB")
    
    def _create_indexes(self):
        """Create indexes for better query performance"""
        try:
            self.stg_collection.create_index([("security_id", 1), ("date", 1)], unique=True)
            self.stg_collection.create_index([("security_id", 1)])
            self.stg_collection.create_index([("symbol", 1)])
            self.stg_collection.create_index([("date", 1)])
            
            self.core_collection.create_index([("security_id", 1), ("date", 1)], unique=True)
            self.core_collection.create_index([("security_id", 1)])
            self.core_collection.create_index([("symbol", 1)])
            self.core_collection.create_index([("date", 1)])
        except Exception as e:
            logger.warning(f"Error creating indexes (may already exist): {e}")
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'session'):
            self.session.close()
    
    def extract_current_month_data(self) -> Tuple[int, int, int]:
        """
        Extract current month's data
        Returns: (saved, updated, skipped)
        """
        today = date.today()
        return self.extract_for_date(today)
    
    def extract_for_date(self, target_date: date) -> Tuple[int, int, int]:
        """
        Extract delisted securities list for specific date (extracts month of that date)
        Args:
            target_date: Date to extract data for (will extract the month of this date)
        Returns:
            (saved, updated, skipped) - number of new records, updated records, and skipped records
        """
        logger.info(f"Extracting data for date {target_date} (month: {target_date.year}/{target_date.month})")
        saved, updated, skipped = self.extract_for_month(target_date.year, target_date.month)
        logger.info(f"Saved: {saved}, Updated: {updated}, Skipped: {skipped}")
        return saved, updated, skipped
    
    def extract_for_month(self, year: int, month: int) -> Tuple[int, int, int]:
        """
        Extract delisted securities list for specific month
        Args:
            year: Year to extract
            month: Month to extract
        Returns:
            (saved, updated, skipped) - number of new records, updated records, and skipped records
        """
        
        try:
            # Build URL with year/month
            url = f"{DELISTED_SECURITIES_LIST_ENDPOINT}/{year}/{month}"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract data
            delisted_securities_list = data.get('delistedSecuritiesList', {})
            results = delisted_securities_list.get('result', [])
            
            if not results:
                logger.debug(f"{year}/{month}: No data")
                return 0, 0, 0
            
            logger.info(f"{year}/{month}: {len(results)} records")
            
            # Use first day of month as date
            list_date = date(year, month, 1)
            
            # Save
            saved, updated, skipped = self._save_batch(results, list_date)
            
            return saved, updated, skipped
            
        except Exception as e:
            logger.error(f"{year}/{month}: {e}")
            return 0, 0, 0
    
    def _save_batch(self, records: List[Dict], list_date: date) -> Tuple[int, int, int]:
        """
        Save batch of records
        Returns: (saved, updated, skipped)
        """
        saved = 0
        updated = 0
        skipped = 0
        
        for record in records:
            try:
                # Extract security_id
                security_id = record.get('securityId')
                
                if not security_id:
                    logger.error(f"No security_id: {record}")
                    skipped += 1
                    continue
                
                # Create document
                doc = self._create_document(record, list_date)
                
                # Upsert document
                filter_dict = {
                    'security_id': security_id,
                    'date': convert_date_to_string(list_date)
                }
                
                was_inserted, was_updated = upsert_document(
                    self.stg_collection,
                    filter_dict,
                    doc
                )
                
                if was_inserted:
                    saved += 1
                elif was_updated:
                    updated += 1
                    
            except Exception as e:
                logger.error(f"Error saving record: {e}")
                skipped += 1
                continue
        
        return saved, updated, skipped
    
    def _create_document(self, record: Dict, list_date: date) -> Dict:
        """Create document for MongoDB"""
        
        return {
            'security_id': record.get('securityId'),
            'security_name': record.get('securityName'),
            'symbol': record.get('symbol'),
            'date_last_trade': convert_date_to_string(parse_date(record.get('dateLastTrade'))),
            'date': convert_date_to_string(list_date)
        }
    
    def truncate_staging(self):
        """
        Truncate staging collection before new extraction
        """
        logger.info("Truncating staging collection...")
        try:
            truncate_collection(self.stg_collection)
            logger.info("Truncated staging collection successfully")
        except Exception as e:
            logger.error(f"Error truncating staging collection: {e}")
            raise
    
    def merge_to_core(self) -> Tuple[int, int]:
        """
        Merge staging to core
        Returns: (inserted, updated)
        """
        logger.info("Merging delisted_securities_list from staging to core...")
        
        inserted = 0
        updated = 0
        
        try:
            # Get all documents from staging
            stg_docs = self.stg_collection.find({})
            
            for stg_doc in stg_docs:
                # Remove _id from staging doc
                doc = {k: v for k, v in stg_doc.items() if k != '_id'}
                
                # Create filter for upsert
                filter_dict = {
                    'security_id': doc['security_id'],
                    'date': doc['date']
                }
                
                # Upsert to core
                was_inserted, was_updated = upsert_document(
                    self.core_collection,
                    filter_dict,
                    doc
                )
                
                if was_inserted:
                    inserted += 1
                elif was_updated:
                    updated += 1
            
            logger.info(f"Merged delisted_securities_list: {inserted} inserted, {updated} updated")
            return (inserted, updated)
            
        except Exception as e:
            logger.error(f"Error merging delisted_securities_list to core: {e}")
            raise


if __name__ == "__main__":
    """Standalone run - extract current month's data"""
    extractor = DelistedSecuritiesListExtractor()
    
    # Extract current month's data
    saved, updated, skipped = extractor.extract_current_month_data()
    logger.info(f"Finished: Saved: {saved}, Updated: {updated}, Skipped: {skipped}")
