"""
Extract securities types from TASE API
Saves data to MongoDB collections
"""

import logging
import requests
from datetime import date
from typing import Dict, List, Tuple

# Import MongoDB utilities
from config import API_BASE_URL, API_KEY
from database import get_collection
from mongo_helpers import (
    truncate_collection, upsert_document,
    convert_date_to_string
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extract_securities_types.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API configuration
SECURITIES_TYPES_ENDPOINT = f"{API_BASE_URL}/basic-securities/securities-types"

# MongoDB collection names
STG_COLLECTION = "stg_securities_types"
CORE_COLLECTION = "core_securities_types"


class SecuritiesTypesExtractor:
    """
    Extract securities types from TASE API
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
        logger.info("Securities Types: %s", SECURITIES_TYPES_ENDPOINT)
        logger.info("Connected to API and MongoDB")
    
    def _create_indexes(self):
        """Create indexes for better query performance"""
        try:
            self.stg_collection.create_index([("security_full_type_code", 1)], unique=True)
            self.stg_collection.create_index([("security_main_type_code", 1)])
            
            self.core_collection.create_index([("security_full_type_code", 1)], unique=True)
            self.core_collection.create_index([("security_main_type_code", 1)])
        except Exception as e:
            logger.warning(f"Error creating indexes (may already exist): {e}")
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'session'):
            self.session.close()
    
    def extract_data(self) -> Tuple[int, int, int]:
        """
        Extract securities types data (uses today's date)
        Returns: (saved, updated, skipped)
        """
        extraction_date = date.today()
        return self.extract_for_date(extraction_date)
    
    def extract_for_date(self, extraction_date: date) -> Tuple[int, int, int]:
        """
        Extract securities types data for specific date
        Args:
            extraction_date: Date to extract data for
        Returns: (saved, updated, skipped)
        """
        logger.info(f"Extracting securities types data for {extraction_date}...")
        saved, updated, skipped = self._extract_and_save(extraction_date)
        logger.info(f"Saved: {saved}, Updated: {updated}, Skipped: {skipped}")
        return saved, updated, skipped
    
    def _extract_and_save(self, extraction_date: date) -> Tuple[int, int, int]:
        """
        Extract and save securities types
        Args:
            extraction_date: Date when data is extracted
        Returns:
            (saved, updated, skipped) - number of new records, updated records, and skipped records
        """
        
        try:
            response = self.session.get(SECURITIES_TYPES_ENDPOINT, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract data
            securities_types = data.get('securitiesTypes', {})
            results = securities_types.get('result', [])
            
            if not results:
                logger.warning("No securities types found")
                return 0, 0, 0
            
            logger.info(f"Found {len(results)} securities types")
            
            # Save
            saved, updated, skipped = self._save_batch(results, extraction_date)
            
            return saved, updated, skipped
            
        except Exception as e:
            logger.error(f"Error extracting securities types: {e}")
            return 0, 0, 0
    
    def _save_batch(self, records: List[Dict], extraction_date: date) -> Tuple[int, int, int]:
        """
        Save batch of records
        Returns: (saved, updated, skipped)
        """
        saved = 0
        updated = 0
        skipped = 0
        
        for record in records:
            try:
                # Extract security_full_type_code
                security_full_type_code = record.get('securityFullTypeCode')
                
                if not security_full_type_code:
                    logger.error(f"No security_full_type_code: {record}")
                    skipped += 1
                    continue
                
                # Create document
                doc = self._create_document(record, extraction_date)
                
                # Upsert document
                filter_dict = {'security_full_type_code': security_full_type_code}
                
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
    
    def _create_document(self, record: Dict, extraction_date: date) -> Dict:
        """Create document for MongoDB"""
        
        return {
            'security_main_type_desc': record.get('securityMainTypeDesc'),
            'security_main_type_code': record.get('securityMainTypeCode'),
            'security_full_type_code': record.get('securityFullTypeCode'),
            'security_type_desc': record.get('securityTypeDesc'),
            'extraction_date': convert_date_to_string(extraction_date)
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
        logger.info("Merging securities_types from staging to core...")
        
        inserted = 0
        updated = 0
        
        try:
            # Get all documents from staging
            stg_docs = self.stg_collection.find({})
            
            for stg_doc in stg_docs:
                # Remove _id from staging doc
                doc = {k: v for k, v in stg_doc.items() if k != '_id'}
                
                # Create filter for upsert
                filter_dict = {'security_full_type_code': doc['security_full_type_code']}
                
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
            
            logger.info(f"Merged securities_types: {inserted} inserted, {updated} updated")
            return (inserted, updated)
            
        except Exception as e:
            logger.error(f"Error merging securities_types to core: {e}")
            raise


if __name__ == "__main__":
    """Standalone run - extract securities types"""
    extractor = SecuritiesTypesExtractor()
    
    # Extract securities types
    saved, updated, skipped = extractor.extract_data()
    logger.info(f"Finished: Saved: {saved}, Updated: {updated}, Skipped: {skipped}")
