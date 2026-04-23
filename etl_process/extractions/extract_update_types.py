"""
Extract update types from TASE API
Saves data to MongoDB collections
"""

import logging
import requests
from datetime import timedelta, date
from typing import Dict, List, Optional, Tuple

# Import MongoDB utilities
from config import API_BASE_URL, API_KEY
from database import get_collection
from mongo_helpers import (
    truncate_collection, upsert_document
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extract_update_types.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API configuration
UPDATE_TYPES_ENDPOINT = f"{API_BASE_URL}/indices-parameters-updates/update-types"

# MongoDB collection names
STG_COLLECTION = "stg_update_types"
CORE_COLLECTION = "core_update_types"


class UpdateTypesExtractor:
    """
    Extract update types from TASE API
    """

    def __init__(self):
        """Initialize extractor"""
        # Setup API session
        self.session = requests.Session()
        self.session.headers.update({
            'ApiKey': API_KEY,
            'Accept': 'application/json',
            'Accept-Language': 'he-IL',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': f'{API_BASE_URL}/',
            'Origin': API_BASE_URL
        })

        # Get MongoDB collections
        self.stg_collection = get_collection(STG_COLLECTION)
        self.core_collection = get_collection(CORE_COLLECTION)
        
        # Create indexes
        self._create_indexes()

        logger.info("API: %s", API_BASE_URL)
        logger.info("Update Types: %s", UPDATE_TYPES_ENDPOINT)
        logger.info("Connected to API and MongoDB")

    def _create_indexes(self):
        """Create indexes for better query performance"""
        try:
            self.stg_collection.create_index([("update_type_id", 1)], unique=True)
            self.core_collection.create_index([("update_type_id", 1)], unique=True)
        except Exception as e:
            logger.warning(f"Error creating indexes (may already exist): {e}")

    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'session'):
            self.session.close()

    def extract_data(self) -> Tuple[int, int, int]:
        """
        Extract update types data (no date parameter needed)
        Returns:
            (saved, updated, skipped) - number of new records, updated records, and skipped records
        """
        try:
            url = UPDATE_TYPES_ENDPOINT

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Extract data
            get_update_types = data.get('getUpdateTypes', {})
            results = get_update_types.get('result', [])

            if not results:
                logger.debug("No data")
                return 0, 0, 0

            logger.info(f"{len(results)} records")

            # Save
            saved, updated, skipped = self._save_batch(results)

            return saved, updated, skipped

        except Exception as e:
            logger.error(f"Error extracting update types: {e}")
            return 0, 0, 0

    def extract_for_date(self, target_date: date) -> Tuple[int, int, int]:
        """
        Extract update types data for a specific date (date parameter is ignored as endpoint doesn't require it)
        Args:
            target_date: Date to extract (ignored - endpoint doesn't require date)
        Returns:
            (saved, updated, skipped) - number of new records, updated records, and skipped records
        """
        # This endpoint doesn't require a date parameter, so we just call extract_data
        return self.extract_data()

    def _save_batch(self, records: List[Dict]) -> Tuple[int, int, int]:
        """
        Save batch of records
        Returns: (saved, updated, skipped)
        """
        saved = 0
        updated = 0
        skipped = 0

        for record in records:
            try:
                # Extract update_type_id
                update_type_id = record.get('updateTypeId')

                if not update_type_id:
                    logger.error(f"No update_type_id: {record}")
                    skipped += 1
                    continue

                # Create document
                doc = self._create_document(record)

                # Upsert document
                filter_dict = {'update_type_id': update_type_id}

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

    def _create_document(self, record: Dict) -> Dict:
        """Create document for MongoDB"""

        return {
            'update_type_id': record.get('updateTypeId'),
            'update_type': record.get('updateType')
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
        logger.info("Merging update_types from staging to core...")

        inserted = 0
        updated = 0

        try:
            # Get all documents from staging
            stg_docs = self.stg_collection.find({})

            for stg_doc in stg_docs:
                # Remove _id from staging doc
                doc = {k: v for k, v in stg_doc.items() if k != '_id'}

                # Create filter for upsert
                filter_dict = {'update_type_id': doc['update_type_id']}

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

            logger.info(f"Merged update_types: {inserted} inserted, {updated} updated")

            return (inserted, updated)

        except Exception as e:
            logger.error(f"Error merging update_types to core: {e}")
            raise


if __name__ == "__main__":
    """Standalone run - extract update types"""
    extractor = UpdateTypesExtractor()

    # Extract update types
    saved, updated, skipped = extractor.extract_data()
    logger.info(f"Finished: Saved: {saved}, Updated: {updated}, Skipped: {skipped}")
