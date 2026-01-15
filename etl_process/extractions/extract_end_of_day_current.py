"""
Extract current daily EOD trading data (last 7 days) from TASE API
Saves data to MongoDB collections
"""

import logging
import requests
from datetime import timedelta, date, datetime
from typing import Dict, List, Optional, Tuple

# Import MongoDB utilities
from config import API_BASE_URL, API_KEY
from database import get_collection
from mongo_helpers import (
    truncate_collection, upsert_document, find_document,
    parse_date, safe_float, safe_int, convert_date_to_string
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extract_current.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API configuration - seven days endpoints
TRADE_DATA_ENDPOINT = f"{API_BASE_URL}/securities/trading/eod/seven-days/by-date"
EX_CODE_ENDPOINT = f"{API_BASE_URL}/securities/trading/eod/seven-days/ex-code"

# MongoDB collection names
STG_TRADE_DATA_COLLECTION = "stg_trade_data"
STG_EX_CODE_COLLECTION = "stg_ex_code"
CORE_TRADE_DATA_COLLECTION = "core_trade_data"
CORE_EX_CODE_COLLECTION = "core_ex_code"


class TaseCurrentDataExtractor:
    """
    Extract current daily trading data from TASE API
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
        self.stg_trade_collection = get_collection(STG_TRADE_DATA_COLLECTION)
        self.stg_ex_code_collection = get_collection(STG_EX_CODE_COLLECTION)
        self.core_trade_collection = get_collection(CORE_TRADE_DATA_COLLECTION)
        self.core_ex_code_collection = get_collection(CORE_EX_CODE_COLLECTION)
        
        # Create indexes for better performance
        self._create_indexes()
        
        logger.info("API: %s", API_BASE_URL)
        logger.info("Trade Data: %s", TRADE_DATA_ENDPOINT)
        logger.info("Ex Codes: %s", EX_CODE_ENDPOINT)
        logger.info("Connected to API and MongoDB")
    
    def _create_indexes(self):
        """Create indexes for better query performance"""
        try:
            # Indexes for staging trade_data
            self.stg_trade_collection.create_index([("security_id", 1), ("trade_date", 1)], unique=True)
            self.stg_trade_collection.create_index([("trade_date", 1)])
            self.stg_trade_collection.create_index([("security_id", 1)])
            self.stg_trade_collection.create_index([("symbol", 1)])
            
            # Indexes for staging ex_code
            self.stg_ex_code_collection.create_index([("ex_code", 1)], unique=True)
            
            # Indexes for core trade_data
            self.core_trade_collection.create_index([("security_id", 1), ("trade_date", 1)], unique=True)
            self.core_trade_collection.create_index([("trade_date", 1)])
            self.core_trade_collection.create_index([("security_id", 1)])
            self.core_trade_collection.create_index([("symbol", 1)])
            
            # Indexes for core ex_code
            self.core_ex_code_collection.create_index([("ex_code", 1)], unique=True)
        except Exception as e:
            logger.warning(f"Error creating indexes (may already exist): {e}")
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'session'):
            self.session.close()
    
    def extract_yesterday_data(self) -> Tuple[int, int, int]:
        """
        Extract yesterday's data
        Returns: (saved, updated, skipped)
        """
        yesterday = date.today() - timedelta(days=1)
        logger.info(f"Extracting data for yesterday: {yesterday}")
        saved, updated, skipped = self.extract_trade_data_for_date(yesterday)
        logger.info(f"Saved: {saved}, Updated: {updated}, Skipped: {skipped}")
        return saved, updated, skipped
    
    def extract_trade_data_for_date(self, trade_date: date) -> Tuple[int, int, int]:
        """
        Extract trading data for specific date
        Args:
            trade_date: Date to extract
        Returns:
            (saved, updated, skipped) - number of new records, updated records, and skipped records
        """
        
        try:
            params = {'date': trade_date.strftime('%Y-%m-%d')}
            
            response = self.session.get(
                TRADE_DATA_ENDPOINT,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract data
            trading_data = data.get('securitiesEndOfDayTradingData', {})
            results = trading_data.get('result', [])
            
            if not results:
                logger.debug(f"{trade_date}: No data")
                return 0, 0, 0
            
            logger.info(f"{trade_date}: {len(results)} records")
            
            # Save
            saved, updated, skipped = self._save_trade_batch(results, trade_date)
            
            return saved, updated, skipped
            
        except Exception as e:
            logger.error(f"{trade_date}: {e}")
            return 0, 0, 0
    
    def _save_trade_batch(self, records: List[Dict], expected_date: date) -> Tuple[int, int, int]:
        """
        Save batch of records
        Returns: (saved, updated, skipped)
        """
        saved = 0
        updated = 0
        skipped = 0
        
        for record in records:
            try:
                # Extract security_id and trade_date
                security_id = record.get('securityId')
                trade_date_str = record.get('tradeDate')
                
                if not security_id or not trade_date_str:
                    logger.error(f"No security_id or trade_date_str: {record}")
                    skipped += 1
                    continue
                
                trade_date = parse_date(trade_date_str)
                if not trade_date:
                    logger.error(f"No trade_date: {trade_date_str}")
                    skipped += 1
                    continue
                
                # Create document
                doc = self._create_trade_document(record, trade_date)
                
                # Upsert document
                filter_dict = {
                    'security_id': security_id,
                    'trade_date': convert_date_to_string(trade_date)
                }
                
                was_inserted, was_updated = upsert_document(
                    self.stg_trade_collection,
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
    
    def _create_trade_document(self, record: Dict, trade_date: date) -> Dict:
        """Create trade data document for MongoDB"""
        
        return {
            'trade_date': convert_date_to_string(trade_date),
            'first_trading_date': convert_date_to_string(parse_date(record.get('firstTradingDate'))),
            'isin': record.get('isin'),
            'change': safe_float(record.get('change')),
            'security_id': record.get('securityId'),
            'turnover': safe_int(record.get('turnover')),
            'closing_price': safe_float(record.get('closingPrice')),
            'base_price': safe_float(record.get('basePrice')),
            'opening_price': safe_float(record.get('openingPrice')),
            'high': safe_float(record.get('high')),
            'low': safe_float(record.get('low')),
            'change_value': safe_float(record.get('changeValue')),
            'transactions_number': safe_int(record.get('transactionsNumber')),
            'volume': safe_int(record.get('volume')),
            'market_cap': safe_int(record.get('marketCap')),
            'min_cont_phase_amount': safe_int(record.get('minContPhaseAmount')),
            'listed_capital': safe_int(record.get('listedCapital')),
            'adjusted_closing_price': safe_float(record.get('adjustedClosingPrice')),
            'ex_code': safe_int(record.get('exCode')),
            'adjustment_coefficient': safe_float(record.get('adjustmentCoefficient')),
            'symbol': record.get('symbol'),
            'market_type': record.get('marketType')
        }
    
    def extract_ex_codes(self) -> int:
        """
        Extract EX codes
        Returns: number of codes saved
        """
        logger.info("Extracting EX codes...")
        
        try:
            response = self.session.get(EX_CODE_ENDPOINT, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            ex_codes_data = data.get('exeCodesResponse', {})
            results = ex_codes_data.get('result', [])
            
            if not results:
                logger.warning("No EX codes found")
                return 0
            
            logger.info(f"Found {len(results)} codes")
            
            saved, updated = self._save_ex_codes(results)
            logger.info(f"Saved {saved} new, {updated} updated")
            
            return len(results)
            
        except Exception as e:
            logger.error(f"Error extracting EX codes: {e}")
            return 0
    
    def _save_ex_codes(self, codes: List[Dict]) -> Tuple[int, int]:
        """Save EX codes"""
        saved = 0
        updated = 0
        
        for code_data in codes:
            try:
                ex_code = safe_int(code_data.get('exCodeId'))
                if not ex_code:
                    continue
                
                # Create document
                doc = {
                    'ex_code': ex_code,
                    'ex_code_type': code_data.get('exCodeType'),
                    'ex_code_description': code_data.get('exCodeDescription')
                }
                
                # Upsert document
                filter_dict = {'ex_code': ex_code}
                was_inserted, was_updated = upsert_document(
                    self.stg_ex_code_collection,
                    filter_dict,
                    doc
                )
                
                if was_inserted:
                    saved += 1
                elif was_updated:
                    updated += 1
                    
            except Exception as e:
                logger.error(f"Error saving EX code: {e}")
                continue
        
        return saved, updated
    
    def truncate_staging_tables(self):
        """
        Truncate staging collections before new extraction
        """
        logger.info("Truncating staging collections...")
        
        try:
            truncate_collection(self.stg_trade_collection)
            truncate_collection(self.stg_ex_code_collection)
            logger.info("All staging collections truncated successfully")
        except Exception as e:
            logger.error(f"Error truncating staging collections: {e}")
            raise
    
    def merge_trade_data_to_core(self) -> Tuple[int, int]:
        """
        Merge staging trade_data to core trade_data
        Returns: (inserted, updated)
        """
        logger.info("Merging trade_data from staging to core...")
        
        inserted = 0
        updated = 0
        
        try:
            # Get all documents from staging
            stg_docs = self.stg_trade_collection.find({})
            
            for stg_doc in stg_docs:
                # Remove _id from staging doc
                doc = {k: v for k, v in stg_doc.items() if k != '_id'}
                
                # Create filter for upsert
                filter_dict = {
                    'security_id': doc['security_id'],
                    'trade_date': doc['trade_date']
                }
                
                # Upsert to core
                was_inserted, was_updated = upsert_document(
                    self.core_trade_collection,
                    filter_dict,
                    doc
                )
                
                if was_inserted:
                    inserted += 1
                elif was_updated:
                    updated += 1
            
            logger.info(f"Merged trade_data: {inserted} inserted, {updated} updated")
            return (inserted, updated)
            
        except Exception as e:
            logger.error(f"Error merging trade_data to core: {e}")
            raise
    
    def merge_ex_code_to_core(self) -> Tuple[int, int]:
        """
        Merge staging ex_code to core ex_code
        Returns: (inserted, updated)
        """
        logger.info("Merging ex_code from staging to core...")
        
        inserted = 0
        updated = 0
        
        try:
            # Get all documents from staging
            stg_docs = self.stg_ex_code_collection.find({})
            
            for stg_doc in stg_docs:
                # Remove _id from staging doc
                doc = {k: v for k, v in stg_doc.items() if k != '_id'}
                
                # Create filter for upsert
                filter_dict = {'ex_code': doc['ex_code']}
                
                # Upsert to core
                was_inserted, was_updated = upsert_document(
                    self.core_ex_code_collection,
                    filter_dict,
                    doc
                )
                
                if was_inserted:
                    inserted += 1
                elif was_updated:
                    updated += 1
            
            logger.info(f"Merged ex_code: {inserted} inserted, {updated} updated")
            return (inserted, updated)
            
        except Exception as e:
            logger.error(f"Error merging ex_code to core: {e}")
            raise


if __name__ == "__main__":
    """Standalone run - extract yesterday's data"""
    extractor = TaseCurrentDataExtractor()
    
    # Extract EX codes
    extractor.extract_ex_codes()
    
    # Extract yesterday's data
    saved, updated, skipped = extractor.extract_yesterday_data()
    logger.info(f"Finished: Saved: {saved}, Updated: {updated}, Skipped: {skipped}")
