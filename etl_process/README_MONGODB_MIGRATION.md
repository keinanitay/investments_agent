# MongoDB Migration - ETL Process

## סיכום השינויים

הפרויקט הומר מ-PostgreSQL ל-MongoDB כדי לעבוד עם ה-backend הקיים.

### קבצים שעודכנו:

1. **`config.py`** - הומר לעבוד עם MongoDB (MONGO_URI, DB_NAME)
2. **`database.py`** - קובץ חדש לחיבור MongoDB (sync)
3. **`mongo_helpers.py`** - קובץ חדש עם helper functions לעבודה עם MongoDB
4. **`main.py`** - הומר לבדיקת חיבור MongoDB
5. **`check_daily_status.py`** - הומר לבדיקת חיבור MongoDB
6. **`requirements.txt`** - עודכן עם pymongo במקום psycopg2-binary ו-SQLAlchemy

### Extractors שהומרו:

1. ✅ `extract_end_of_day_current.py` - הומר ל-MongoDB
2. ✅ `extract_traded_securities_list.py` - הומר ל-MongoDB
3. ✅ `extract_companies_list.py` - הומר ל-MongoDB

### Extractors שצריך להמיר:

יש עוד כ-15 extractors שצריך להמיר לפי אותו דפוס:
- extract_delisted_securities_list.py
- extract_illiquid_maintenance_suspension_list.py
- extract_trading_code_list.py
- extract_securities_types.py
- extract_public_holdings_indices.py
- extract_expected_changes_ians_float.py
- extract_expected_changes_weight_factor.py
- extract_index_components_extended.py
- extract_parameters_update_schedule.py
- extract_indices_constituents_update.py
- extract_capital_listed_for_trading_eod.py
- extract_constituents_update_lists.py
- extract_bond_data.py
- extract_universe_constituents_update.py
- extract_update_types.py

## הגדרת סביבה

### משתני סביבה נדרשים ב-.env:

```bash
# MongoDB
MONGO_URI=mongodb://localhost:27017
DB_NAME=tase_bot_db

# TASE API
TASE_API_BASE_URL=https://openapi.tase.co.il
TASE_API_KEY=your_api_key_here
```

### התקנת חבילות:

```bash
cd etl_process
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## הרצת Test

```bash
cd etl_process
source venv/bin/activate
python test_mongo_extraction.py
```

## מבנה MongoDB Collections

במקום schemas של PostgreSQL, MongoDB משתמש ב-collections:

- **Staging collections**: `stg_*` (למשל: `stg_trade_data`, `stg_ex_code`)
- **Core collections**: `core_*` (למשל: `core_trade_data`, `core_ex_code`)

## הערות חשובות

1. **תאריכים**: נשמרים כ-strings (ISO format) ב-MongoDB
2. **Indexes**: נוצרים אוטומטית ב-`_create_indexes()` בכל extractor
3. **JSONB fields**: הופכים ל-dict/list ב-MongoDB
4. **Unique constraints**: מיושמים באמצעות unique indexes

## דפוס המרה ל-extractors נוספים

1. החלף imports מ-SQLAlchemy ל-MongoDB helpers
2. החלף `self.engine` ו-`self.Session` ב-`self.stg_collection` ו-`self.core_collection`
3. החלף `_create_record` ב-`_create_document` (מחזיר dict)
4. החלף `_save_batch` לשימוש ב-`upsert_document`
5. החלף `truncate_staging` לשימוש ב-`truncate_collection`
6. החלף `merge_to_core` לשימוש ב-`upsert_document` עם לולאה

## סטטוס

✅ MongoDB connection - עובד
✅ Collections creation - עובד
✅ Indexes creation - עובד
✅ Test extraction script - עובד
⚠️ API connection - 503 error (כנראה זמני, צריך לבדוק עם API key תקין)

