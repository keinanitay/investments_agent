"""
סקריפט לשליפת נתוני מסחר היסטוריים מ-API של הבורסה
משוך נתונים מ-2015-01-01 עד 2025-11-04, מדלג על שישי-שבת
"""

import os
import requests
from datetime import date, timedelta
from typing import Optional, Dict, List
import time
import logging

from config import API_BASE_URL, API_KEY
from database import get_collection
from mongo_helpers import (
    upsert_document, parse_date, safe_float, safe_int, convert_date_to_string
)

# הגדרת logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extract_history.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# בניית endpoints
EX_CODES_ENDPOINT = f"{API_BASE_URL}/securities/trading/eod/history/ten-years/ex-code"
TRADE_DATA_ENDPOINT = f"{API_BASE_URL}/securities/trading/eod/history/ten-years/by-date"

# MongoDB collection names
EX_CODES_COLLECTION = "historical_ex_code"
TRADE_DATA_COLLECTION = "historical_trade_data"

# תאריכים
START_DATE = date(2015, 1, 1)
END_DATE = date(2025, 11, 4)

logger.info(f"🔧 API: {API_BASE_URL}")
logger.info(f"🔧 Trade Data: {TRADE_DATA_ENDPOINT}")
logger.info(f"🔧 Ex Codes: {EX_CODES_ENDPOINT}")
logger.info(f"📅 טווח: {START_DATE} → {END_DATE}")


class TaseAPIExtractor:
    """מחלקה לשליפת נתונים מ-API"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'ApiKey': API_KEY,
            'Accept': 'application/json',
            'accept-language': 'he-IL',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': f'{API_BASE_URL}/',
            'Origin': API_BASE_URL
        })
        
        # Get MongoDB collections
        self.ex_codes_collection = get_collection(EX_CODES_COLLECTION)
        self.trade_data_collection = get_collection(TRADE_DATA_COLLECTION)
        
        # Create indexes
        self._create_indexes()
        
        logger.info("✅ מחובר ל-API ול-MongoDB")
    
    def _create_indexes(self):
        """Create indexes for better query performance"""
        try:
            self.ex_codes_collection.create_index([("ex_code", 1)], unique=True)
            self.trade_data_collection.create_index([("security_id", 1), ("trade_date", 1)], unique=True)
            self.trade_data_collection.create_index([("security_id", 1)])
            self.trade_data_collection.create_index([("trade_date", 1)])
        except Exception as e:
            logger.warning(f"Error creating indexes (may already exist): {e}")
    
    def __del__(self):
        """סגירת חיבורים"""
        if hasattr(self, 'session'):
            self.session.close()
    
    def extract_ex_codes(self) -> int:
        """שליפת קודי EX"""
        logger.info("📋 מושך קודי EX...")
        
        try:
            response = self.session.get(EX_CODES_ENDPOINT, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # חילוץ נתונים
            ex_codes_list = data.get('exeCodesResponse', {}).get('result', [])
            
            if not ex_codes_list:
                logger.warning("⚠️  לא נמצאו קודים")
                return 0
            
            logger.info(f"✅ נמצאו {len(ex_codes_list)} קודים")
            
            # שמירה
            saved = 0
            updated = 0
            
            for item in ex_codes_list:
                try:
                    ex_code_id = item.get('exCodeId')
                    if not ex_code_id:
                        continue
                    
                    # Create document
                    doc = {
                        'ex_code': int(ex_code_id),
                        'ex_code_type': item.get('exCodeType'),
                        'ex_code_description': item.get('exCodeDescription')
                    }
                    
                    # Upsert document
                    filter_dict = {'ex_code': int(ex_code_id)}
                    
                    was_inserted, was_updated = upsert_document(
                        self.ex_codes_collection,
                        filter_dict,
                        doc
                    )
                    
                    if was_inserted:
                        saved += 1
                    elif was_updated:
                        updated += 1
                        
                except Exception as e:
                    logger.error(f"❌ שגיאה: {e}")
                    continue
            
            logger.info(f"💾 נשמרו {saved} חדשים, {updated} עודכנו")
            return saved + updated
            
        except Exception as e:
            logger.error(f"❌ שגיאה בשליפת קודי EX: {e}")
            return 0
    
    def extract_trade_data_by_date_range(self, start_date: date, end_date: date) -> int:
        """
        שליפת נתוני מסחר לטווח תאריכים
        מדלג על שישי-שבת
        """
        logger.info(f"📊 מתחיל שליפת נתוני מסחר: {start_date} → {end_date}")
        
        total_saved = 0
        total_updated = 0
        total_skipped = 0
        total_empty = 0
        
        current_date = start_date
        
        while current_date <= end_date:
            # בדיקה אם זה שישי או שבת (4=Friday, 5=Saturday)
            if current_date.weekday() in [4, 5]:
                logger.debug(f"⏭️  מדלג על {current_date} (סוף שבוע)")
                total_skipped += 1
                current_date += timedelta(days=1)
                continue
            
            # שליפה לתאריך ספציפי
            try:
                saved, updated = self.extract_trade_data_for_date(current_date)
                
                if saved == 0 and updated == 0:
                    total_empty += 1
                else:
                    total_saved += saved
                    total_updated += updated
                
                # המתנה קצרה בין בקשות
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"❌ שגיאה בתאריך {current_date}: {e}")
            
            current_date += timedelta(days=1)
        
        logger.info("="*70)
        logger.info(f"✅ הושלם!")
        logger.info(f"📊 נשמרו: {total_saved} | עודכנו: {total_updated}")
        logger.info(f"📊 ימי סוף שבוע: {total_skipped} | ימים ריקים: {total_empty}")
        logger.info("="*70)
        
        return total_saved + total_updated
    
    def extract_trade_data_for_date(self, trade_date: date) -> tuple:
        """שליפת נתוני מסחר לתאריך בודד"""
        
        try:
            params = {'date': trade_date.strftime('%Y-%m-%d')}
            
            response = self.session.get(
                TRADE_DATA_ENDPOINT,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # חילוץ נתונים
            trading_data = data.get('securitiesEndOfDayTradingData', {})
            results = trading_data.get('result', [])
            
            if not results:
                logger.debug(f"📭 {trade_date}: אין נתונים")
                return 0, 0
            
            logger.info(f"📅 {trade_date}: {len(results)} רשומות")
            
            # שמירה
            saved, updated = self._save_trade_batch(results, trade_date)
            
            return saved, updated
            
        except Exception as e:
            logger.error(f"❌ {trade_date}: {e}")
            return 0, 0
    
    def _save_trade_batch(self, records: List[Dict], expected_date: date) -> tuple:
        """שמירת batch של רשומות"""
        saved = 0
        updated = 0
        
        for record in records:
            try:
                security_id = record.get('securityId')
                trade_date = parse_date(record.get('tradeDate'))
                
                if not security_id or not trade_date:
                    continue
                
                # Create document
                doc = self._create_trade_document(record, trade_date)
                
                # Upsert document
                filter_dict = {
                    'security_id': security_id,
                    'trade_date': convert_date_to_string(trade_date)
                }
                
                was_inserted, was_updated = upsert_document(
                    self.trade_data_collection,
                    filter_dict,
                    doc
                )
                
                if was_inserted:
                    saved += 1
                elif was_updated:
                    updated += 1
                
            except Exception as e:
                logger.error(f"❌ שגיאה ברשומה: {e}")
                continue
        
        return saved, updated
    
    def _create_trade_document(self, record: Dict, trade_date: date) -> Dict:
        """יצירת document עבור MongoDB"""
        
        return {
            'trade_date': convert_date_to_string(trade_date),
            'first_trading_date': convert_date_to_string(parse_date(record.get('firstTradingDate'))) if record.get('firstTradingDate') else None,
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


def main():
    """פונקציה ראשית"""
    logger.info("="*70)
    logger.info("🚀 מתחיל שליפת נתונים היסטוריים")
    logger.info("="*70)
    
    extractor = TaseAPIExtractor()
    
    # שלב 1: קודי EX
    logger.info("\n📋 שלב 1: שליפת קודי EX")
    ex_count = extractor.extract_ex_codes()
    
    # שלב 2: נתוני מסחר
    logger.info(f"\n📊 שלב 2: שליפת נתוני מסחר")
    logger.info(f"תאריכים: {START_DATE} → {END_DATE}")
    logger.info(f"מדלג על ימי שישי-שבת")
    logger.info("")
    
    trade_count = extractor.extract_trade_data_by_date_range(START_DATE, END_DATE)
    
    # סיכום
    logger.info("\n" + "="*70)
    logger.info("✅ תהליך השליפה הושלם!")
    logger.info(f"📊 קודי EX: {ex_count}")
    logger.info(f"📊 רשומות מסחר: {trade_count}")
    logger.info("="*70)


if __name__ == "__main__":
    main()
