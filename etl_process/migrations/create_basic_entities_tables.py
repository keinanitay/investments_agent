"""
Migration Script: Create basic entities tables
Creates:
- Schema: stg and core (if not exists)
- Tables: traded_securities_list, delisted_securities_list, companies_list, illiquid_maintenance_suspension_list
"""

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

# Import tables
import sys
import os
# Add parent directory to path to import db_schema
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_schema import (
    Base,
    StgTradedSecuritiesList,
    CoreTradedSecuritiesList,
    StgDelistedSecuritiesList,
    CoreDelistedSecuritiesList,
    StgCompaniesList,
    CoreCompaniesList,
    StgIlliquidMaintenanceSuspensionList,
    CoreIlliquidMaintenanceSuspensionList,
    StgTradingCodeList,
    CoreTradingCodeList,
    StgSecuritiesTypes,
    CoreSecuritiesTypes,
    StgPublicHoldingsIndices,
    CorePublicHoldingsIndices,
    StgExpectedChangesIansFloat,
    CoreExpectedChangesIansFloat,
    StgExpectedChangesWeightFactor,
    CoreExpectedChangesWeightFactor,
    StgIndexComponentsExtended,
    CoreIndexComponentsExtended,
    StgParametersUpdateSchedule,
    CoreParametersUpdateSchedule,
    StgIndicesConstituentsUpdate,
    CoreIndicesConstituentsUpdate,
    StgCapitalListedForTradingEod,
    CoreCapitalListedForTradingEod,
    StgConstituentsUpdateLists,
    CoreConstituentsUpdateLists,
    StgBondData,
    CoreBondData,
    StgUniverseConstituentsUpdate,
    CoreUniverseConstituentsUpdate,
    StgUpdateTypes,
    CoreUpdateTypes
)
from config import DB_CONN

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("migration_basic_entities.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

STG_SCHEMA = 'stg'
CORE_SCHEMA = 'core'


def run_migration():
    """Run migration - create schema and tables"""
    logger.info("Starting migration for basic entities tables...")

    engine = create_engine(DB_CONN)

    with engine.connect() as conn:
        # Step 1: Create schemas if not exist
        logger.info(f"Creating schemas: {STG_SCHEMA} and {CORE_SCHEMA}")
        try:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {STG_SCHEMA};"))
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {CORE_SCHEMA};"))
            conn.commit()
            logger.info("Schemas created successfully")
        except ProgrammingError as e:
            logger.error(f"Error creating schemas: {e}")
            conn.rollback()
            return

        # Step 2: Create staging tables and indexes
        logger.info("Creating staging tables and indexes...")
        try:
            Base.metadata.create_all(engine, tables=[
                StgTradedSecuritiesList.__table__,
                StgDelistedSecuritiesList.__table__,
                StgCompaniesList.__table__,
                StgIlliquidMaintenanceSuspensionList.__table__,
                StgTradingCodeList.__table__,
                StgSecuritiesTypes.__table__,
                StgPublicHoldingsIndices.__table__,
                StgExpectedChangesIansFloat.__table__,
                StgExpectedChangesWeightFactor.__table__,
                StgIndexComponentsExtended.__table__,
                StgParametersUpdateSchedule.__table__,
                StgIndicesConstituentsUpdate.__table__,
                StgCapitalListedForTradingEod.__table__,
                StgConstituentsUpdateLists.__table__,
                StgBondData.__table__,
                StgUniverseConstituentsUpdate.__table__,
                StgUpdateTypes.__table__
            ])
            conn.commit()
            logger.info("Staging tables and indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating staging tables: {e}")
            conn.rollback()
            return

        # Step 3: Create core tables and indexes
        logger.info("Creating core tables and indexes...")
        try:
            Base.metadata.create_all(engine, tables=[
                CoreTradedSecuritiesList.__table__,
                CoreDelistedSecuritiesList.__table__,
                CoreCompaniesList.__table__,
                CoreIlliquidMaintenanceSuspensionList.__table__,
                CoreTradingCodeList.__table__,
                CoreSecuritiesTypes.__table__,
                CorePublicHoldingsIndices.__table__,
                CoreExpectedChangesIansFloat.__table__,
                CoreExpectedChangesWeightFactor.__table__,
                CoreIndexComponentsExtended.__table__,
                CoreParametersUpdateSchedule.__table__,
                CoreIndicesConstituentsUpdate.__table__,
                CoreCapitalListedForTradingEod.__table__,
                CoreConstituentsUpdateLists.__table__,
                CoreBondData.__table__,
                CoreUniverseConstituentsUpdate.__table__,
                CoreUpdateTypes.__table__
            ])
            conn.commit()
            logger.info("Core tables and indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating core tables: {e}")
            conn.rollback()
            return

    # Step 4: Verify staging tables were created
    logger.info("\nVerifying staging tables were created...")
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = '{STG_SCHEMA}'
            AND table_name IN ('traded_securities_list', 'delisted_securities_list', 'companies_list', 'illiquid_maintenance_suspension_list', 'trading_code_list', 'securities_types', 'public_holdings_indices', 'expected_changes_ians_float', 'expected_changes_weight_factor', 'index_components_extended', 'parameters_update_schedule', 'indices_constituents_update', 'capital_listed_for_trading_eod', 'constituents_update_lists', 'bond_data', 'universe_constituents_update', 'update_types')
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result]
        logger.info(f"\nStaging tables created in schema {STG_SCHEMA}:")
        for table in tables:
            logger.info(f"   - {table}")
        conn.rollback()  # Rollback the implicit transaction from SELECT

    # Step 5: Verify core tables were created
    logger.info("\nVerifying core tables were created...")
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = '{CORE_SCHEMA}'
            AND table_name IN ('traded_securities_list', 'delisted_securities_list', 'companies_list', 'illiquid_maintenance_suspension_list', 'trading_code_list', 'securities_types', 'public_holdings_indices', 'expected_changes_ians_float', 'expected_changes_weight_factor', 'index_components_extended', 'parameters_update_schedule', 'indices_constituents_update', 'capital_listed_for_trading_eod', 'constituents_update_lists', 'bond_data', 'universe_constituents_update', 'update_types')
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result]
        logger.info(f"\nCore tables created in schema {CORE_SCHEMA}:")
        for table in tables:
            logger.info(f"   - {table}")
        conn.rollback()  # Rollback the implicit transaction from SELECT

    # Step 6: Verify indexes were created
    logger.info("\nChecking indexes...")
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT
                schemaname,
                tablename,
                indexname
            FROM pg_indexes
            WHERE schemaname IN ('{STG_SCHEMA}', '{CORE_SCHEMA}')
            AND tablename IN ('traded_securities_list', 'delisted_securities_list', 'companies_list', 'illiquid_maintenance_suspension_list', 'trading_code_list')
            ORDER BY schemaname, tablename, indexname;
        """))
        logger.info(f"\nIndexes created:")
        for row in result:
            logger.info(f"   - {row[0]}.{row[1]}.{row[2]}")
        conn.rollback()  # Rollback the implicit transaction from SELECT

    logger.info("\n" + "=" * 70)
    logger.info("Migration for basic entities tables completed successfully!")
    logger.info("=" * 70)


def run_rollback():
    """Rollback migration - delete tables"""
    logger.info("Starting rollback...")

    engine = create_engine(DB_CONN)

    with engine.connect() as conn:
        try:
            logger.info("Dropping tables...")

            # Drop staging tables
            tables_to_drop = [
                f"{STG_SCHEMA}.traded_securities_list",
                f"{STG_SCHEMA}.delisted_securities_list",
                f"{STG_SCHEMA}.companies_list",
                f"{STG_SCHEMA}.illiquid_maintenance_suspension_list",
                f"{STG_SCHEMA}.trading_code_list",
                f"{STG_SCHEMA}.securities_types",
                f"{STG_SCHEMA}.public_holdings_indices",
                f"{STG_SCHEMA}.expected_changes_ians_float",
                f"{STG_SCHEMA}.expected_changes_weight_factor",
                f"{STG_SCHEMA}.index_components_extended",
                f"{STG_SCHEMA}.parameters_update_schedule",
                f"{STG_SCHEMA}.indices_constituents_update",
                f"{STG_SCHEMA}.capital_listed_for_trading_eod",
                f"{STG_SCHEMA}.constituents_update_lists",
                f"{STG_SCHEMA}.bond_data",
                f"{STG_SCHEMA}.universe_constituents_update",
                f"{STG_SCHEMA}.update_types"
            ]

            for table in tables_to_drop:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
                    logger.info(f"Dropped {table}")
                except Exception as e:
                    logger.warning(f"Error dropping {table}: {e}")

            # Drop core tables
            tables_to_drop = [
                f"{CORE_SCHEMA}.traded_securities_list",
                f"{CORE_SCHEMA}.delisted_securities_list",
                f"{CORE_SCHEMA}.companies_list",
                f"{CORE_SCHEMA}.illiquid_maintenance_suspension_list",
                f"{CORE_SCHEMA}.trading_code_list",
                f"{CORE_SCHEMA}.securities_types",
                f"{CORE_SCHEMA}.public_holdings_indices",
                f"{CORE_SCHEMA}.expected_changes_ians_float",
                f"{CORE_SCHEMA}.expected_changes_weight_factor",
                f"{CORE_SCHEMA}.index_components_extended",
                f"{CORE_SCHEMA}.parameters_update_schedule",
                f"{CORE_SCHEMA}.indices_constituents_update",
                f"{CORE_SCHEMA}.capital_listed_for_trading_eod",
                f"{CORE_SCHEMA}.constituents_update_lists",
                f"{CORE_SCHEMA}.bond_data",
                f"{CORE_SCHEMA}.universe_constituents_update",
                f"{CORE_SCHEMA}.update_types"
            ]

            for table in tables_to_drop:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
                    logger.info(f"Dropped {table}")
                except Exception as e:
                    logger.warning(f"Error dropping {table}: {e}")

            conn.commit()
            logger.info("Tables dropped successfully.")
        except ProgrammingError as e:
            logger.error(f"Error dropping tables: {e}")
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
