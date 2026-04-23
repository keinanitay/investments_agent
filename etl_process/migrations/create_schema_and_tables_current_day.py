"""
Migration Script: Create schema and tables for current daily data
Creates:
- Schema: current_date_eod_data
- Table: trade_data_current
- Table: ex_code_current
"""

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

# Import new tables
import sys
import os
# Add parent directory to path to import db_schema
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_schema import Base, StgTradeData, StgExCode
from config import DB_CONN

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("migration_current.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Build connection string
conn_string = DB_CONN

SCHEMA_NAME = 'stg'


def run_migration():
    """Run migration - create schema and tables"""
    logger.info("Starting migration for current daily data...")
    
    engine = create_engine(conn_string)
    
    with engine.connect() as conn:
        # Step 1: Create schema
        logger.info(f"Creating schema: {SCHEMA_NAME}")
        try:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME};"))
            conn.commit()
            logger.info("Schema created successfully")
        except ProgrammingError as e:
            logger.error(f"Error creating schema: {e}")
            conn.rollback()
            return
        
        # Step 2: Create tables and indexes
        logger.info("Creating tables and indexes...")
        try:
            Base.metadata.create_all(engine, tables=[StgTradeData.__table__, StgExCode.__table__])
            conn.commit()
            logger.info("Tables and indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            conn.rollback()
            return
    
    # Step 3: Verify tables were created
    logger.info("\nVerifying tables were created...")
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = '{SCHEMA_NAME}'
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result]
        logger.info(f"\nTables created in schema {SCHEMA_NAME}:")
        for table in tables:
            logger.info(f"   - {table}")
        conn.rollback()  # Rollback the implicit transaction from SELECT
    
    # Step 4: Verify indexes were created
    logger.info("\nChecking indexes...")
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT 
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = '{SCHEMA_NAME}'
            ORDER BY tablename, indexname;
        """))
        logger.info(f"\nIndexes created:")
        for row in result:
            logger.info(f"   - {row[0]}.{row[1]}")
        conn.rollback()  # Rollback the implicit transaction from SELECT
    
    logger.info("\n" + "=" * 70)
    logger.info("Migration for daily data completed successfully!")
    logger.info("=" * 70)


def run_rollback():
    """Rollback migration - delete schema and tables"""
    logger.info("Starting rollback...")
    
    engine = create_engine(conn_string)
    
    with engine.connect() as conn:
        try:
            logger.info(f"Deleting schema {SCHEMA_NAME} and all its contents...")
            conn.execute(text(f"DROP SCHEMA IF EXISTS {SCHEMA_NAME} CASCADE;"))
            conn.commit()
            logger.info(f"Schema {SCHEMA_NAME} deleted successfully.")
        except ProgrammingError as e:
            logger.error(f"Error deleting schema: {e}")
            conn.rollback()
    
    logger.info("=" * 70)
    logger.info("Rollback completed!")
    logger.info("=" * 70)


if __name__ == "__main__":
    import sys
    
    # Check if rollback should be run
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        run_rollback()
    else:
        run_migration()
