"""
Extract bond data from TASE API
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
    parse_date, safe_int, convert_date_to_string
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extract_bond_data.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API configuration
BOND_DATA_ENDPOINT = f"{API_BASE_URL}/indices-parameters-updates/bond-data"

# MongoDB collection names
STG_COLLECTION = "stg_bond_data"
CORE_COLLECTION = "core_bond_data"


class BondDataExtractor:
    """
    Extract bond data from TASE API
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
        logger.info("Bond Data: %s", BOND_DATA_ENDPOINT)
        logger.info("Connected to API and MongoDB")

    def _create_indexes(self):
        """Create indexes for better query performance"""
        try:
            self.stg_collection.create_index([("security_id", 1), ("first_trading_date", 1)], unique=True)
            self.stg_collection.create_index([("security_id", 1)])
            self.stg_collection.create_index([("first_trading_date", 1)])
            
            self.core_collection.create_index([("security_id", 1), ("first_trading_date", 1)], unique=True)
            self.core_collection.create_index([("security_id", 1)])
            self.core_collection.create_index([("first_trading_date", 1)])
        except Exception as e:
            logger.warning(f"Error creating indexes (may already exist): {e}")

    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'session'):
            self.session.close()

    def extract_for_date(self, trade_date: date) -> Tuple[int, int, int]:
        """
        Extract bond data for specific date
        Args:
            trade_date: Date to extract (year/month/day)
        Returns:
            (saved, updated, skipped) - number of new records, updated records, and skipped records
        """

        try:
            # Build URL with year/month/day
            url = f"{BOND_DATA_ENDPOINT}/{trade_date.year}/{trade_date.month}/{trade_date.day}"

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Extract data
            get_bond_data = data.get('getBondData', {})
            results = get_bond_data.get('result', [])

            if not results:
                logger.debug(f"{trade_date}: No data")
                return 0, 0, 0

            logger.info(f"{trade_date}: {len(results)} records")

            # Save
            saved, updated, skipped = self._save_batch(results, trade_date)

            return saved, updated, skipped

        except Exception as e:
            logger.error(f"{trade_date}: {e}")
            return 0, 0, 0

    def _save_batch(self, records: List[Dict], expected_date: date) -> Tuple[int, int, int]:
        """
        Save batch of records
        Returns: (saved, updated, skipped)
        """
        saved = 0
        updated = 0
        skipped = 0

        for record in records:
            try:
                # Extract security_id and first_trading_date
                security_id = record.get('securityId')
                first_trading_date_str = record.get('firstTradingDate')

                if not security_id:
                    logger.error(f"No security_id: {record}")
                    skipped += 1
                    continue

                # Convert security_id to string (can be string or number)
                security_id_str = str(security_id) if security_id is not None else None

                # Parse first_trading_date
                first_trading_date = parse_date(first_trading_date_str) if first_trading_date_str else None
                first_trading_date_str = convert_date_to_string(first_trading_date) if first_trading_date else None

                # Create document
                doc = self._create_document(record, expected_date, first_trading_date_str)

                # Upsert document
                filter_dict = {
                    'security_id': security_id_str,
                    'first_trading_date': first_trading_date_str
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

    def _create_document(self, record: Dict, extraction_date: date, first_trading_date_str: Optional[str]) -> Dict:
        """Create document for MongoDB"""

        security_id = record.get('securityId')
        security_id_str = str(security_id) if security_id is not None else None

        return {
            'date': convert_date_to_string(extraction_date),
            'security_id': security_id_str,
            'first_trading_date': first_trading_date_str,
            'market_cap': record.get('marketCap'),
            'average_market_cap_without_redemption': safe_int(record.get('averageMarketCapWithoutRedemption')),
            'exit_from_tel_bond': record.get('exitFromTelBond'),
            'interest_type': record.get('interestType'),
            'indices': record.get('indices')  # Save as array directly
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
        logger.info("Merging bond_data from staging to core...")

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
                    'first_trading_date': doc['first_trading_date']
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

            logger.info(f"Merged bond_data: {inserted} inserted, {updated} updated")

            return (inserted, updated)

        except Exception as e:
            logger.error(f"Error merging bond_data to core: {e}")
            raise


if __name__ == "__main__":
    """Standalone run - extract yesterday's data"""
    extractor = BondDataExtractor()

    # Extract yesterday's data
    yesterday = date.today() - timedelta(days=1)
    saved, updated, skipped = extractor.extract_for_date(yesterday)
    logger.info(f"Finished: Saved: {saved}, Updated: {updated}, Skipped: {skipped}")
