"""
Migration Script: Remove year_sequence_id column and indexes from trade_data tables
Removes:
- Column: year_sequence_id from core.trade_data
- Column: year_sequence_id from stg.trade_data_current
- Column: year_sequence_id from ten_years_back_data.trade_data
- Index: idx_year_sequence from core.trade_data
- Index: idx_current_year_sequence from stg.trade_data_current
- Index: idx_year_sequence from ten_years_back_data.trade_data
"""

import logging
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONN

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("migration_remove_year_sequence_id.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Tables to modify
TABLES = [
    {'schema': 'core', 'table': 'trade_data', 'index': 'idx_year_sequence'},
    {'schema': 'stg', 'table': 'trade_data_current', 'index': 'idx_current_year_sequence'},
    {'schema': 'ten_years_back_data', 'table': 'trade_data', 'index': 'idx_year_sequence'}
]


def run_migration():
    """Run migration - remove year_sequence_id column and indexes"""
    logger.info("Starting migration to remove year_sequence_id...")
    
    engine = create_engine(DB_CONN)
    
    with engine.connect() as conn:
        try:
            for table_info in TABLES:
                schema = table_info['schema']
                table = table_info['table']
                index = table_info['index']
                full_table_name = f"{schema}.{table}"
                
                # Step 1: Drop index if exists
                logger.info(f"Dropping index {index} from {full_table_name}...")
                try:
                    conn.execute(text(f"DROP INDEX IF EXISTS {schema}.{index};"))
                    logger.info(f"Index {index} dropped successfully")
                except Exception as e:
                    logger.warning(f"Error dropping index {index}: {e}")
                
                # Step 2: Drop column if exists
                logger.info(f"Dropping column year_sequence_id from {full_table_name}...")
                try:
                    conn.execute(text(f"ALTER TABLE {full_table_name} DROP COLUMN IF EXISTS year_sequence_id;"))
                    logger.info(f"Column year_sequence_id dropped successfully from {full_table_name}")
                except Exception as e:
                    logger.warning(f"Error dropping column from {full_table_name}: {e}")
            
            conn.commit()
            logger.info("Migration completed successfully")
            
        except Exception as e:
            logger.error(f"Error during migration: {e}")
            conn.rollback()
            raise
    
    # Step 3: Verify columns were removed
    logger.info("\nVerifying columns were removed...")
    with engine.connect() as conn:
        for table_info in TABLES:
            schema = table_info['schema']
            table = table_info['table']
            full_table_name = f"{schema}.{table}"
            
            result = conn.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = '{schema}' 
                AND table_name = '{table}'
                AND column_name = 'year_sequence_id';
            """))
            
            columns = [row[0] for row in result]
            if columns:
                logger.warning(f"Column year_sequence_id still exists in {full_table_name}")
            else:
                logger.info(f"✓ Column year_sequence_id removed from {full_table_name}")
            
            conn.rollback()  # Rollback the implicit transaction from SELECT
    
    # Step 4: Verify indexes were removed
    logger.info("\nVerifying indexes were removed...")
    with engine.connect() as conn:
        for table_info in TABLES:
            schema = table_info['schema']
            index = table_info['index']
            
            result = conn.execute(text(f"""
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = '{schema}'
                AND indexname = '{index}';
            """))
            
            indexes = [row[0] for row in result]
            if indexes:
                logger.warning(f"Index {index} still exists in schema {schema}")
            else:
                logger.info(f"✓ Index {index} removed from schema {schema}")
            
            conn.rollback()  # Rollback the implicit transaction from SELECT
    
    logger.info("\n" + "=" * 70)
    logger.info("Migration to remove year_sequence_id completed successfully!")
    logger.info("=" * 70)


def run_rollback():
    """
    Rollback migration - recreate year_sequence_id column and indexes
    Note: This will recreate the column as nullable since we don't have the original data
    """
    logger.info("Starting rollback - recreating year_sequence_id column and indexes...")
    
    engine = create_engine(DB_CONN)
    
    with engine.connect() as conn:
        try:
            for table_info in TABLES:
                schema = table_info['schema']
                table = table_info['table']
                index = table_info['index']
                full_table_name = f"{schema}.{table}"
                
                # Step 1: Recreate column
                logger.info(f"Recreating column year_sequence_id in {full_table_name}...")
                try:
                    conn.execute(text(f"""
                        ALTER TABLE {full_table_name} 
                        ADD COLUMN IF NOT EXISTS year_sequence_id BIGINT UNIQUE;
                    """))
                    logger.info(f"Column year_sequence_id recreated in {full_table_name}")
                except Exception as e:
                    logger.warning(f"Error recreating column in {full_table_name}: {e}")
                
                # Step 2: Recreate index
                logger.info(f"Recreating index {index} on {full_table_name}...")
                try:
                    conn.execute(text(f"""
                        CREATE INDEX IF NOT EXISTS {index} 
                        ON {full_table_name}(year_sequence_id);
                    """))
                    logger.info(f"Index {index} recreated successfully")
                except Exception as e:
                    logger.warning(f"Error recreating index {index}: {e}")
            
            conn.commit()
            logger.info("Rollback completed successfully")
            
        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            conn.rollback()
            raise
    
    logger.info("=" * 70)
    logger.info("Rollback completed!")
    logger.info("=" * 70)


if __name__ == "__main__":
    import sys
    
    # Check if rollback should be run
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        confirm = input("⚠️  Are you sure you want to recreate year_sequence_id? (yes/no): ")
        if confirm.lower() == 'yes':
            run_rollback()
        else:
            logger.info("Rollback cancelled")
    else:
        run_migration()

