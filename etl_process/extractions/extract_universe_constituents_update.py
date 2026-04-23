"""
Extract universe constituents update from TASE API
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
        logging.FileHandler("extract_universe_constituents_update.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API configuration
UNIVERSE_CONSTITUENTS_UPDATE_ENDPOINT = f"{API_BASE_URL}/indices-parameters-updates/universe-constituents-update"

# MongoDB collection names
STG_COLLECTION = "stg_universe_constituents_update"
CORE_COLLECTION = "core_universe_constituents_update"


class UniverseConstituentsUpdateExtractor:
    """
    Extract universe constituents update from TASE API
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
        logger.info("Universe Constituents Update: %s", UNIVERSE_CONSTITUENTS_UPDATE_ENDPOINT)
        logger.info("Connected to API and MongoDB")

    def _create_indexes(self):
        """Create indexes for better query performance"""
        try:
            self.stg_collection.create_index([
                ("security_id", 1),
                ("effective_date", 1),
                ("universe_name", 1)
            ], unique=True)
            self.stg_collection.create_index([("security_id", 1)])
            self.stg_collection.create_index([("universe_name", 1)])
            
            self.core_collection.create_index([
                ("security_id", 1),
                ("effective_date", 1),
                ("universe_name", 1)
            ], unique=True)
            self.core_collection.create_index([("security_id", 1)])
            self.core_collection.create_index([("universe_name", 1)])
        except Exception as e:
            logger.warning(f"Error creating indexes (may already exist): {e}")

    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'session'):
            self.session.close()

    def extract_for_universe_and_date(self, universe_name: str, target_date: date) -> Tuple[int, int, int]:
        """
        Extract universe constituents update for specific universe and date (extracts month of that date)
        Args:
            universe_name: Universe name to extract
            target_date: Date to extract data for (will extract the month of this date)
        Returns:
            (saved, updated, skipped) - number of new records, updated records, and skipped records
        """
        logger.info(f"Extracting data for universe {universe_name} and date {target_date} (month: {target_date.year}/{target_date.month})")
        saved, updated, skipped = self.extract_for_universe_and_month(universe_name, target_date.year, target_date.month)
        logger.info(f"Saved: {saved}, Updated: {updated}, Skipped: {skipped}")
        return saved, updated, skipped

    def extract_for_universe_and_month(self, universe_name: str, year: int, month: int) -> Tuple[int, int, int]:
        """
        Extract universe constituents update for specific universe and month
        Args:
            universe_name: Universe name to extract
            year: Year to extract
            month: Month to extract
        Returns:
            (saved, updated, skipped) - number of new records, updated records, and skipped records
        """

        try:
            # Build URL with universe_name/year/month
            url = f"{UNIVERSE_CONSTITUENTS_UPDATE_ENDPOINT}/{universe_name}/{year}/{month}"

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Extract data
            universe_constituents_update = data.get('universeConstituentsUpdate', {})
            results = universe_constituents_update.get('result', [])

            if not results:
                logger.debug(f"{universe_name}/{year}/{month}: No data")
                return 0, 0, 0

            logger.info(f"{universe_name}/{year}/{month}: {len(results)} records")

            # Create date from year/month (first day of month)
            extraction_date = date(year, month, 1)

            # Save
            saved, updated, skipped = self._save_batch(results, universe_name, extraction_date)

            return saved, updated, skipped

        except Exception as e:
            logger.error(f"{universe_name}/{year}/{month}: {e}")
            return 0, 0, 0

    def _save_batch(self, records: List[Dict], universe_name: str, extraction_date: date) -> Tuple[int, int, int]:
        """
        Save batch of records
        Returns: (saved, updated, skipped)
        """
        saved = 0
        updated = 0
        skipped = 0

            for record in records:
                try:
                    # Extract security_id and effective_date
                    security_id = record.get('securityId')
                effective_date = parse_date(record.get('effectiveDate'))

                    if not security_id:
                        logger.error(f"No security_id: {record}")
                        skipped += 1
                        continue

                # Create document
                doc = self._create_document(record, universe_name, extraction_date)

                # Upsert document
                filter_dict = {
                    'security_id': safe_int(security_id),
                    'effective_date': convert_date_to_string(effective_date) if effective_date else None,
                    'universe_name': universe_name
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

    def _create_document(self, record: Dict, universe_name: str, extraction_date: date) -> Dict:
        """Create document for MongoDB"""

        return {
            'date': convert_date_to_string(extraction_date),
            'universe_name': universe_name,
            'security_id': safe_int(record.get('securityId')),
            'security_name': record.get('securityName'),
            'symbol': record.get('symbol'),
            'isin': record.get('isin'),
            'index_universe_name': record.get('indexUniverseName'),
            'security_status': record.get('securityStatus'),
            'update_type': record.get('updateType'),
            'market_sector': record.get('marketSector'),
            'announcement_date': convert_date_to_string(parse_date(record.get('announcementDate'))) if record.get('announcementDate') else None,
            'effective_date': convert_date_to_string(parse_date(record.get('effectiveDate'))) if record.get('effectiveDate') else None,
            'new_ians': record.get('newIans'),
            'new_index_adjusted_free_float': record.get('newIndexAdjustedFreeFloat'),
            'free_float_semi_annual': record.get('freeFloatSemiAnnual'),
            'free_float_monthly': record.get('freeFloatMonthly'),
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
            'median_velocity_turnover': safe_float(record.get('medianVelocityTurnover')),
            'liquidity_ratio': safe_float(record.get('liquidityRatio'))
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
        logger.info("Merging universe_constituents_update from staging to core...")

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
                    'effective_date': doc['effective_date'],
                    'universe_name': doc['universe_name']
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

                logger.info(f"Merged universe_constituents_update: {inserted} inserted, {updated} updated")

                return (inserted, updated)

            except Exception as e:
                logger.error(f"Error merging universe_constituents_update to core: {e}")
                raise


if __name__ == "__main__":
    """Standalone run - extract current month's data for a specific universe"""
    extractor = UniverseConstituentsUpdateExtractor()

    # Extract current month's data for a specific universe (example)
    # Note: Replace 'TA-35' with the actual universe name you want to extract
    today = date.today()
    universe_name = "TA-35"  # This should be configured or passed as parameter
    saved, updated, skipped = extractor.extract_for_universe_and_date(universe_name, today)
    logger.info(f"Finished: Saved: {saved}, Updated: {updated}, Skipped: {skipped}")
