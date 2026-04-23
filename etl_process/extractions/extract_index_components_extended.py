"""
Extract index components extended from TASE API
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
    safe_float, safe_int, safe_bool, convert_date_to_string
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extract_index_components_extended.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API configuration
INDEX_COMPONENTS_EXTENDED_ENDPOINT = f"{API_BASE_URL}/indices-parameters-updates/index-components-extended"

# MongoDB collection names
STG_COLLECTION = "stg_index_components_extended"
CORE_COLLECTION = "core_index_components_extended"


class IndexComponentsExtendedExtractor:
    """
    Extract index components extended from TASE API
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
        logger.info("Index Components Extended: %s", INDEX_COMPONENTS_EXTENDED_ENDPOINT)
        logger.info("Connected to API and MongoDB")

    def _create_indexes(self):
        """Create indexes for better query performance"""
        try:
            self.stg_collection.create_index([("security_id", 1), ("index_id", 1), ("date", 1)], unique=True)
            self.stg_collection.create_index([("security_id", 1)])
            self.stg_collection.create_index([("index_id", 1)])
            self.stg_collection.create_index([("date", 1)])
            
            self.core_collection.create_index([("security_id", 1), ("index_id", 1), ("date", 1)], unique=True)
            self.core_collection.create_index([("security_id", 1)])
            self.core_collection.create_index([("index_id", 1)])
            self.core_collection.create_index([("date", 1)])
        except Exception as e:
            logger.warning(f"Error creating indexes (may already exist): {e}")

    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'session'):
            self.session.close()

    def extract_for_date(self, trade_date: date) -> Tuple[int, int, int]:
        """
        Extract index components extended for specific date
        Args:
            trade_date: Date to extract (year/month/day)
        Returns:
            (saved, updated, skipped) - number of new records, updated records, and skipped records
        """

        try:
            # Build URL with year/month/day
            url = f"{INDEX_COMPONENTS_EXTENDED_ENDPOINT}/{trade_date.year}/{trade_date.month}/{trade_date.day}"

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Extract data
            index_component_extended = data.get('indexComponentExtended', {})
            results = index_component_extended.get('result', [])

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
                # Extract security_id and index_id
                security_id = record.get('securityId')
                index_id = record.get('indexId')

                if not security_id:
                    logger.error(f"No security_id: {record}")
                    skipped += 1
                    continue

                # Create document
                doc = self._create_document(record, expected_date)

                # Upsert document
                filter_dict = {
                    'security_id': safe_int(security_id),
                    'index_id': str(index_id) if index_id else None,
                    'date': convert_date_to_string(expected_date)
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

    def _create_document(self, record: Dict, trade_date: date) -> Dict:
        """Create document for MongoDB"""

        return {
            'date': convert_date_to_string(trade_date),
            'security_id': safe_int(record.get('securityId')),
            'security_name': record.get('securityName'),
            'symbol': record.get('symbol'),
            'isin': record.get('isin'),
            'index_id': str(record.get('indexId')) if record.get('indexId') else None,
            'last_ians_update': record.get('lastIansUpdate'),
            'weight': safe_float(record.get('weight')),
            'market_cap': safe_float(record.get('marketCap')),
            'base_price': safe_float(record.get('basePrice')),
            'closing_price': safe_float(record.get('closingPrice')),
            'is_ex': safe_bool(record.get('isEX')),
            'semi_ann_daily_turnover_avg': safe_float(record.get('semiAnnDailyTurnoverAvg')),
            'semi_ann_median_turnover': safe_float(record.get('semiAnnMedianTurnover')),
            'free_float_rate': safe_float(record.get('freeFloatRate')),
            'free_float_percent': safe_float(record.get('freeFloatPercent')),
            'ians': safe_int(record.get('ians')),
            'index_adjusted_free_float': safe_float(record.get('indexAdjustedFreeFloat')),
            'weight_factor': safe_float(record.get('weightFactor')),
            'free_float_market_cap': safe_float(record.get('freeFloatMarketCap')),
            'liquidity_ratio': safe_float(record.get('LiquidityRatio')),
            'weighted_factor': safe_float(record.get('WeightedFactor'))
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
        logger.info("Merging index_components_extended from staging to core...")

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
                    'index_id': doc['index_id'],
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

            logger.info(f"Merged index_components_extended: {inserted} inserted, {updated} updated")

            return (inserted, updated)

        except Exception as e:
            logger.error(f"Error merging index_components_extended to core: {e}")
            raise


if __name__ == "__main__":
    """Standalone run - extract yesterday's data"""
    extractor = IndexComponentsExtendedExtractor()

    # Extract yesterday's data
    yesterday = date.today() - timedelta(days=1)
    saved, updated, skipped = extractor.extract_for_date(yesterday)
    logger.info(f"Finished: Saved: {saved}, Updated: {updated}, Skipped: {skipped}")
