"""
Extract parameters update schedule from TASE API
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
    truncate_collection, upsert_document,
    parse_date, convert_date_to_string
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extract_parameters_update_schedule.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API configuration
PARAMETERS_UPDATE_SCHEDULE_ENDPOINT = f"{API_BASE_URL}/indices-parameters-updates/parameters-update-schedule"

# MongoDB collection names
STG_COLLECTION = "stg_parameters_update_schedule"
CORE_COLLECTION = "core_parameters_update_schedule"


class ParametersUpdateScheduleExtractor:
    """
    Extract parameters update schedule from TASE API
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
        logger.info("Parameters Update Schedule: %s", PARAMETERS_UPDATE_SCHEDULE_ENDPOINT)
        logger.info("Connected to API and MongoDB")

    def _create_indexes(self):
        """Create indexes for better query performance"""
        try:
            self.stg_collection.create_index([
                ("record_date", 1),
                ("effective_date", 1),
                ("index_category", 1),
                ("update_type", 1)
            ], unique=True)
            self.stg_collection.create_index([("record_date", 1)])
            self.stg_collection.create_index([("effective_date", 1)])
            
            self.core_collection.create_index([
                ("record_date", 1),
                ("effective_date", 1),
                ("index_category", 1),
                ("update_type", 1)
            ], unique=True)
            self.core_collection.create_index([("record_date", 1)])
            self.core_collection.create_index([("effective_date", 1)])
        except Exception as e:
            logger.warning(f"Error creating indexes (may already exist): {e}")

    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'session'):
            self.session.close()

    def extract_for_date(self, target_date: date) -> Tuple[int, int, int]:
        """
        Extract parameters update schedule for specific date (extracts month of that date)
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
        Extract parameters update schedule for specific month
        Args:
            year: Year to extract
            month: Month to extract
        Returns:
            (saved, updated, skipped) - number of new records, updated records, and skipped records
        """

        try:
            # Build URL with year/month
            url = f"{PARAMETERS_UPDATE_SCHEDULE_ENDPOINT}/{year}/{month}"

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Extract data
            parameters_update_schedule = data.get('parametersUpdateSchedule', {})
            results = parameters_update_schedule.get('result', [])

            if not results:
                logger.debug(f"{year}/{month}: No data")
                return 0, 0, 0

            logger.info(f"{year}/{month}: {len(results)} records")

            # Create date from year/month (first day of month)
            extraction_date = date(year, month, 1)

            # Save
            saved, updated, skipped = self._save_batch(results, extraction_date)

            return saved, updated, skipped

        except Exception as e:
            logger.error(f"{year}/{month}: {e}")
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
                # Extract key fields for unique constraint
                record_date = parse_date(record.get('recordDate'))
                effective_date = parse_date(record.get('effectiveDate'))
                index_category = record.get('indexCategory')
                update_type = record.get('updateType')

                if not record_date or not effective_date or not index_category or not update_type:
                    logger.error(f"Missing required fields: {record}")
                    skipped += 1
                    continue

                # Create document
                doc = self._create_document(record, extraction_date)

                # Upsert document
                filter_dict = {
                    'record_date': convert_date_to_string(record_date),
                    'effective_date': convert_date_to_string(effective_date),
                    'index_category': index_category,
                    'update_type': update_type
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

    def _create_document(self, record: Dict, extraction_date: date) -> Dict:
        """Create document for MongoDB"""

        return {
            'date': convert_date_to_string(extraction_date),
            'index_category': record.get('indexCategory'),
            'update_type': record.get('updateType'),
            'record_date': convert_date_to_string(parse_date(record.get('recordDate'))) if record.get('recordDate') else None,
            'announcement_date': convert_date_to_string(parse_date(record.get('announcementDate'))) if record.get('announcementDate') else None,
            'effective_date': convert_date_to_string(parse_date(record.get('effectiveDate'))) if record.get('effectiveDate') else None,
            'free_float_record_date': convert_date_to_string(parse_date(record.get('freeFloatRecordDate'))) if record.get('freeFloatRecordDate') else None
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
        logger.info("Merging parameters_update_schedule from staging to core...")

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
                    'record_date': doc['record_date'],
                    'effective_date': doc['effective_date'],
                    'index_category': doc['index_category'],
                    'update_type': doc['update_type']
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

            logger.info(f"Merged parameters_update_schedule: {inserted} inserted, {updated} updated")

            return (inserted, updated)

        except Exception as e:
            logger.error(f"Error merging parameters_update_schedule to core: {e}")
            raise


if __name__ == "__main__":
    """Standalone run - extract current month's data"""
    extractor = ParametersUpdateScheduleExtractor()

    # Extract current month's data
    today = date.today()
    saved, updated, skipped = extractor.extract_for_date(today)
    logger.info(f"Finished: Saved: {saved}, Updated: {updated}, Skipped: {skipped}")
