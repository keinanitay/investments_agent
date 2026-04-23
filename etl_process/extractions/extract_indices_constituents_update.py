"""
Extract indices constituents update from TASE API
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
    parse_date, safe_float, safe_int, safe_bool, convert_date_to_string
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extract_indices_constituents_update.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API configuration
INDICES_CONSTITUENTS_UPDATE_ENDPOINT = f"{API_BASE_URL}/indices-parameters-updates/indices-constituents-update"

# MongoDB collection names
STG_COLLECTION = "stg_indices_constituents_update"
CORE_COLLECTION = "core_indices_constituents_update"


class IndicesConstituentsUpdateExtractor:
    """
    Extract indices constituents update from TASE API
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
        logger.info("Indices Constituents Update: %s", INDICES_CONSTITUENTS_UPDATE_ENDPOINT)
        logger.info("Connected to API and MongoDB")

    def _create_indexes(self):
        """Create indexes for better query performance"""
        try:
            self.stg_collection.create_index([
                ("security_id", 1),
                ("index_id", 1),
                ("effective_date", 1),
                ("announcement_date", 1)
            ], unique=True)
            self.stg_collection.create_index([("security_id", 1)])
            self.stg_collection.create_index([("index_id", 1)])
            
            self.core_collection.create_index([
                ("security_id", 1),
                ("index_id", 1),
                ("effective_date", 1),
                ("announcement_date", 1)
            ], unique=True)
            self.core_collection.create_index([("security_id", 1)])
            self.core_collection.create_index([("index_id", 1)])
        except Exception as e:
            logger.warning(f"Error creating indexes (may already exist): {e}")

    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'session'):
            self.session.close()

    def extract_for_date(self, target_date: date) -> Tuple[int, int, int]:
        """
        Extract indices constituents update for specific date (extracts month of that date)
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
        Extract indices constituents update for specific month
        Args:
            year: Year to extract
            month: Month to extract
        Returns:
            (saved, updated, skipped) - number of new records, updated records, and skipped records
        """

        try:
            # Build URL with year/month
            url = f"{INDICES_CONSTITUENTS_UPDATE_ENDPOINT}/{year}/{month}"

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Extract data
            indices_constituents_update = data.get('indicesConstituentsUpdate', {})
            results = indices_constituents_update.get('result', [])

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
                    security_id = record.get('securityId')
                    index_id = record.get('indexId')
                effective_date = parse_date(record.get('effectiveDate'))
                announcement_date = parse_date(record.get('announcementDate'))

                    if not security_id:
                        logger.error(f"No security_id: {record}")
                        skipped += 1
                        continue

                # Create document
                doc = self._create_document(record, extraction_date)

                # Upsert document
                filter_dict = {
                    'security_id': safe_int(security_id),
                    'index_id': safe_int(index_id) if index_id else None,
                    'effective_date': convert_date_to_string(effective_date) if effective_date else None,
                    'announcement_date': convert_date_to_string(announcement_date) if announcement_date else None
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
            'security_id': safe_int(record.get('securityId')),
            'security_name': record.get('securityName'),
            'symbol': record.get('symbol'),
            'isin': record.get('isin'),
            'index_id': safe_int(record.get('indexId')),
            'index_name': record.get('indexName'),
            'security_status_index': record.get('securityStatusIndex'),
            'update_type': record.get('updateType'),
            'market_sector': record.get('marketSector'),
            'announcement_date': convert_date_to_string(parse_date(record.get('announcementDate'))) if record.get('announcementDate') else None,
            'effective_date': convert_date_to_string(parse_date(record.get('effectiveDate'))) if record.get('effectiveDate') else None,
            'new_ians': safe_int(record.get('newIans')),
            'expected_fnv_pre_rebalance_bonds_only': safe_int(record.get('expectedFNVPreRebalanceBondsOnly')),
            'new_index_adjusted_free_float': record.get('newIndexAdjustedFreeFloat'),
            'new_weight_factor': safe_float(record.get('newWeightFactor')),
            'free_float_semi_annual': safe_float(record.get('freeFloatSemiAnnual')),
            'free_float_monthly': safe_float(record.get('freeFloatMonthly')),
            'average_free_float': safe_float(record.get('averageFreeFloat')),
            'is_illiquid_securities_candidate': safe_bool(record.get('isIlliquidSecuritiesCandidate')),
            'is_maintenance_list': safe_bool(record.get('isMaintenanceList')),
            'is_suspended_securities': safe_bool(record.get('isSuspendedSecurities')),
            'semi_annual_average_daily_turnover': safe_float(record.get('semiAnnualAverageDailyTurnover')),
            'semi_annual_median_turnover': safe_float(record.get('semiAnnualMedianTurnover')),
            'capital_listed_trading': safe_int(record.get('capitalListedTrading')),
            'average_market_cap': safe_float(record.get('averageMarketCap')),
            'average_price': safe_float(record.get('averagePrice')),
            'closing_price': safe_float(record.get('closingPrice')),
            'liquidity_ratio': safe_float(record.get('liquidityRatio')),
            'weighted_factor': safe_float(record.get('weightedFactor')),
            'median_velocity_turnover': safe_float(record.get('medianVelocityTurnover'))
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
        logger.info("Merging indices_constituents_update from staging to core...")

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
                    'effective_date': doc['effective_date'],
                    'announcement_date': doc['announcement_date']
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

                logger.info(f"Merged indices_constituents_update: {inserted} inserted, {updated} updated")

                return (inserted, updated)

            except Exception as e:
                logger.error(f"Error merging indices_constituents_update to core: {e}")
                raise


if __name__ == "__main__":
    """Standalone run - extract current month's data"""
    extractor = IndicesConstituentsUpdateExtractor()

    # Extract current month's data
    today = date.today()
    saved, updated, skipped = extractor.extract_for_date(today)
    logger.info(f"Finished: Saved: {saved}, Updated: {updated}, Skipped: {skipped}")
