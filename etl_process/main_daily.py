"""
Main script for daily run - extract EOD data for a specific date
"""

import logging
import argparse
from datetime import datetime, date, timedelta
from extractions.extract_end_of_day_current import TaseCurrentDataExtractor
from extractions.extract_traded_securities_list import TradedSecuritiesListExtractor
from extractions.extract_delisted_securities_list import DelistedSecuritiesListExtractor
from extractions.extract_companies_list import CompaniesListExtractor
from extractions.extract_illiquid_maintenance_suspension_list import IlliquidMaintenanceSuspensionListExtractor
from extractions.extract_trading_code_list import TradingCodeListExtractor
from extractions.extract_securities_types import SecuritiesTypesExtractor
from extractions.extract_public_holdings_indices import PublicHoldingsIndicesExtractor
from extractions.extract_expected_changes_ians_float import ExpectedChangesIansFloatExtractor
from extractions.extract_expected_changes_weight_factor import ExpectedChangesWeightFactorExtractor
from extractions.extract_index_components_extended import IndexComponentsExtendedExtractor
from extractions.extract_parameters_update_schedule import ParametersUpdateScheduleExtractor
from extractions.extract_indices_constituents_update import IndicesConstituentsUpdateExtractor
from extractions.extract_capital_listed_for_trading_eod import CapitalListedForTradingEodExtractor
from extractions.extract_constituents_update_lists import ConstituentsUpdateListsExtractor
from extractions.extract_bond_data import BondDataExtractor
from extractions.extract_universe_constituents_update import UniverseConstituentsUpdateExtractor
from extractions.extract_update_types import UpdateTypesExtractor

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("daily_run.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main(target_date: date = None):
    """
    Main function for daily run
    Args:
        target_date: Date to extract data for. If None, defaults to November 4, 2025.
    """
    if target_date is None:
        target_date = date.today()

    start_time = datetime.now()
    logger.info("=" * 70)
    logger.info(f"Starting daily run for date: {target_date}")
    logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    try:
        # Create extractors
        trade_extractor = TaseCurrentDataExtractor()
        traded_securities_extractor = TradedSecuritiesListExtractor()
        delisted_securities_extractor = DelistedSecuritiesListExtractor()
        companies_extractor = CompaniesListExtractor()
        illiquid_extractor = IlliquidMaintenanceSuspensionListExtractor()
        trading_code_extractor = TradingCodeListExtractor()
        securities_types_extractor = SecuritiesTypesExtractor()
        public_holdings_extractor = PublicHoldingsIndicesExtractor()
        expected_changes_extractor = ExpectedChangesIansFloatExtractor()
        expected_changes_weight_extractor = ExpectedChangesWeightFactorExtractor()
        index_components_extended_extractor = IndexComponentsExtendedExtractor()
        parameters_update_schedule_extractor = ParametersUpdateScheduleExtractor()
        indices_constituents_update_extractor = IndicesConstituentsUpdateExtractor()
        capital_listed_eod_extractor = CapitalListedForTradingEodExtractor()
        constituents_update_lists_extractor = ConstituentsUpdateListsExtractor()
        bond_data_extractor = BondDataExtractor()
        universe_constituents_extractor = UniverseConstituentsUpdateExtractor()
        update_types_extractor = UpdateTypesExtractor()

        # Step 1: Truncate trade staging tables
        logger.info("\nStep 1: Truncating trade staging tables")
        trade_extractor.truncate_staging_tables()
        logger.info("Trade staging tables truncated")

        # Step 2: Extract EX codes
        logger.info("\nStep 2: Extracting EX codes")
        ex_count = trade_extractor.extract_ex_codes()
        logger.info(f"Extracted {ex_count} EX codes")

        # Step 3: Extract trading data for target date
        logger.info(f"\nStep 3: Extracting trading data for {target_date}")
        trade_saved, trade_updated, trade_skipped = trade_extractor.extract_trade_data_for_date(target_date)

        # Step 4: Truncate traded securities staging
        logger.info("\nStep 4: Truncating traded securities staging table")
        traded_securities_extractor.truncate_staging()
        logger.info("Traded securities staging table truncated")

        # Step 5: Extract traded securities list
        logger.info(f"\nStep 5: Extracting traded securities list for {target_date}")
        traded_sec_saved, traded_sec_updated, traded_sec_skipped = traded_securities_extractor.extract_for_date(target_date)

        # Step 6: Truncate delisted securities staging
        logger.info("\nStep 6: Truncating delisted securities staging table")
        delisted_securities_extractor.truncate_staging()
        logger.info("Delisted securities staging table truncated")

        # Step 7: Extract delisted securities list
        logger.info(f"\nStep 7: Extracting delisted securities list for {target_date}")
        delisted_sec_saved, delisted_sec_updated, delisted_sec_skipped = delisted_securities_extractor.extract_for_date(target_date)

        # Step 8: Truncate companies staging
        logger.info("\nStep 8: Truncating companies staging table")
        companies_extractor.truncate_staging()
        logger.info("Companies staging table truncated")

        # Step 9: Extract companies list
        logger.info(f"\nStep 9: Extracting companies list for {target_date}")
        companies_saved, companies_updated, companies_skipped = companies_extractor.extract_for_date(target_date)

        # Step 10: Truncate illiquid maintenance and suspension staging
        logger.info("\nStep 10: Truncating illiquid maintenance and suspension staging table")
        illiquid_extractor.truncate_staging()
        logger.info("Illiquid maintenance and suspension staging table truncated")

        # Step 11: Extract illiquid maintenance and suspension list
        logger.info(f"\nStep 11: Extracting illiquid maintenance and suspension list for {target_date}")
        illiquid_saved, illiquid_updated, illiquid_skipped = illiquid_extractor.extract_for_date(target_date)

        # Step 12: Truncate trading code staging
        logger.info("\nStep 12: Truncating trading code staging table")
        trading_code_extractor.truncate_staging()
        logger.info("Trading code staging table truncated")

        # Step 13: Extract trading code list
        logger.info(f"\nStep 13: Extracting trading code list for {target_date}")
        trading_code_saved, trading_code_updated, trading_code_skipped = trading_code_extractor.extract_for_date(target_date)

        # Step 14: Truncate securities types staging
        logger.info("\nStep 14: Truncating securities types staging table")
        securities_types_extractor.truncate_staging()
        logger.info("Securities types staging table truncated")

        # Step 15: Extract securities types
        logger.info(f"\nStep 15: Extracting securities types for {target_date}")
        securities_types_saved, securities_types_updated, securities_types_skipped = securities_types_extractor.extract_for_date(target_date)

        # Step 16: Truncate public holdings indices staging
        logger.info("\nStep 16: Truncating public holdings indices staging table")
        public_holdings_extractor.truncate_staging()
        logger.info("Public holdings indices staging table truncated")

        # Step 17: Extract public holdings indices
        logger.info(f"\nStep 17: Extracting public holdings indices for {target_date}")
        public_holdings_saved, public_holdings_updated, public_holdings_skipped = public_holdings_extractor.extract_for_date(target_date)

        # Step 18: Truncate expected changes IANS float staging
        logger.info("\nStep 18: Truncating expected changes IANS float staging table")
        expected_changes_extractor.truncate_staging()
        logger.info("Expected changes IANS float staging table truncated")

        # Step 19: Extract expected changes IANS float
        logger.info(f"\nStep 19: Extracting expected changes IANS float for {target_date}")
        expected_changes_saved, expected_changes_updated, expected_changes_skipped = expected_changes_extractor.extract_for_date(target_date)

        # Step 20: Truncate expected changes weight factor staging
        logger.info("\nStep 20: Truncating expected changes weight factor staging table")
        expected_changes_weight_extractor.truncate_staging()
        logger.info("Expected changes weight factor staging table truncated")

        # Step 21: Extract expected changes weight factor
        logger.info(f"\nStep 21: Extracting expected changes weight factor for {target_date}")
        expected_changes_weight_saved, expected_changes_weight_updated, expected_changes_weight_skipped = expected_changes_weight_extractor.extract_for_date(target_date)

        # Step 22: Truncate index components extended staging
        logger.info("\nStep 22: Truncating index components extended staging table")
        index_components_extended_extractor.truncate_staging()
        logger.info("Index components extended staging table truncated")

        # Step 23: Extract index components extended
        logger.info(f"\nStep 23: Extracting index components extended for {target_date}")
        index_components_extended_saved, index_components_extended_updated, index_components_extended_skipped = index_components_extended_extractor.extract_for_date(target_date)

        # Step 24: Truncate parameters update schedule staging
        logger.info("\nStep 24: Truncating parameters update schedule staging table")
        parameters_update_schedule_extractor.truncate_staging()
        logger.info("Parameters update schedule staging table truncated")

        # Step 25: Extract parameters update schedule
        logger.info(f"\nStep 25: Extracting parameters update schedule for {target_date}")
        parameters_update_schedule_saved, parameters_update_schedule_updated, parameters_update_schedule_skipped = parameters_update_schedule_extractor.extract_for_date(target_date)

        # Step 26: Truncate indices constituents update staging
        logger.info("\nStep 26: Truncating indices constituents update staging table")
        indices_constituents_update_extractor.truncate_staging()
        logger.info("Indices constituents update staging table truncated")

        # Step 27: Extract indices constituents update
        logger.info(f"\nStep 27: Extracting indices constituents update for {target_date}")
        indices_constituents_update_saved, indices_constituents_update_updated, indices_constituents_update_skipped = indices_constituents_update_extractor.extract_for_date(target_date)

        # Step 28: Truncate capital listed for trading EOD staging
        logger.info("\nStep 28: Truncating capital listed for trading EOD staging table")
        capital_listed_eod_extractor.truncate_staging()
        logger.info("Capital listed for trading EOD staging table truncated")

        # Step 29: Extract capital listed for trading EOD
        logger.info(f"\nStep 29: Extracting capital listed for trading EOD for {target_date}")
        capital_listed_eod_saved, capital_listed_eod_updated, capital_listed_eod_skipped = capital_listed_eod_extractor.extract_for_date(target_date)

        # Step 30: Truncate constituents update lists staging
        logger.info("\nStep 30: Truncating constituents update lists staging table")
        constituents_update_lists_extractor.truncate_staging()
        logger.info("Constituents update lists staging table truncated")

        # Step 31: Extract constituents update lists
        logger.info(f"\nStep 31: Extracting constituents update lists for {target_date}")
        constituents_update_lists_saved, constituents_update_lists_updated, constituents_update_lists_skipped = constituents_update_lists_extractor.extract_for_date(target_date)

        # Step 32: Truncate bond data staging
        logger.info("\nStep 32: Truncating bond data staging table")
        bond_data_extractor.truncate_staging()
        logger.info("Bond data staging table truncated")

        # Step 33: Extract bond data
        logger.info(f"\nStep 33: Extracting bond data for {target_date}")
        bond_data_saved, bond_data_updated, bond_data_skipped = bond_data_extractor.extract_for_date(target_date)

        # Step 34: Truncate universe constituents update staging
        logger.info("\nStep 34: Truncating universe constituents update staging table")
        universe_constituents_extractor.truncate_staging()
        logger.info("Universe constituents update staging table truncated")

        # Step 35: Extract universe constituents update
        # NOTE: This endpoint requires a universe_name parameter.
        # You need to define which universes to extract (e.g., 'TA-35', 'TA-90', etc.)
        # For now, this is commented out. Uncomment and configure the universes list as needed.
        logger.info(f"\nStep 35: Extracting universe constituents update for {target_date}")
        # TODO: Define the list of universes to extract
        # universes_to_extract = ['TA-35', 'TA-90', 'TA-125']  # Example - configure as needed
        # universe_constituents_saved = 0
        # universe_constituents_updated = 0
        # universe_constituents_skipped = 0
        # for universe_name in universes_to_extract:
        #     saved, updated, skipped = universe_constituents_extractor.extract_for_universe_and_date(universe_name, target_date)
        #     universe_constituents_saved += saved
        #     universe_constituents_updated += updated
        #     universe_constituents_skipped += skipped
        universe_constituents_saved = 0
        universe_constituents_updated = 0
        universe_constituents_skipped = 0
        logger.info("Universe constituents update extraction skipped - configure universes list first")

        # Step 36: Truncate update types staging
        logger.info("\nStep 36: Truncating update types staging table")
        update_types_extractor.truncate_staging()
        logger.info("Update types staging table truncated")

        # Step 37: Extract update types
        logger.info(f"\nStep 37: Extracting update types for {target_date}")
        update_types_saved, update_types_updated, update_types_skipped = update_types_extractor.extract_for_date(target_date)

        # Step 38: Merge staging to core
        logger.info("\nStep 38: Merging staging to core")
        trade_inserted, trade_updated_merge = trade_extractor.merge_trade_data_to_core()
        ex_inserted, ex_updated = trade_extractor.merge_ex_code_to_core()
        traded_sec_inserted, traded_sec_updated_merge = traded_securities_extractor.merge_to_core()
        delisted_sec_inserted, delisted_sec_updated_merge = delisted_securities_extractor.merge_to_core()
        companies_inserted, companies_updated_merge = companies_extractor.merge_to_core()
        illiquid_inserted, illiquid_updated_merge = illiquid_extractor.merge_to_core()
        trading_code_inserted, trading_code_updated_merge = trading_code_extractor.merge_to_core()
        securities_types_inserted, securities_types_updated_merge = securities_types_extractor.merge_to_core()
        public_holdings_inserted, public_holdings_updated_merge = public_holdings_extractor.merge_to_core()
        expected_changes_inserted, expected_changes_updated_merge = expected_changes_extractor.merge_to_core()
        expected_changes_weight_inserted, expected_changes_weight_updated_merge = expected_changes_weight_extractor.merge_to_core()
        index_components_extended_inserted, index_components_extended_updated_merge = index_components_extended_extractor.merge_to_core()
        parameters_update_schedule_inserted, parameters_update_schedule_updated_merge = parameters_update_schedule_extractor.merge_to_core()
        indices_constituents_update_inserted, indices_constituents_update_updated_merge = indices_constituents_update_extractor.merge_to_core()
        capital_listed_eod_inserted, capital_listed_eod_updated_merge = capital_listed_eod_extractor.merge_to_core()
        constituents_update_lists_inserted, constituents_update_lists_updated_merge = constituents_update_lists_extractor.merge_to_core()
        bond_data_inserted, bond_data_updated_merge = bond_data_extractor.merge_to_core()
        universe_constituents_inserted, universe_constituents_updated_merge = universe_constituents_extractor.merge_to_core()
        update_types_inserted, update_types_updated_merge = update_types_extractor.merge_to_core()

        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("\n" + "=" * 70)
        logger.info("Daily run completed successfully!")
        logger.info("=" * 70)
        logger.info(f"Summary:")
        logger.info(f"   EX codes extracted: {ex_count}")
        logger.info(f"   Trade data - New: {trade_saved}, Updated: {trade_updated}, Skipped: {trade_skipped}")
        logger.info(f"   Traded securities list - New: {traded_sec_saved}, Updated: {traded_sec_updated}, Skipped: {traded_sec_skipped}")
        logger.info(f"   Delisted securities list - New: {delisted_sec_saved}, Updated: {delisted_sec_updated}, Skipped: {delisted_sec_skipped}")
        logger.info(f"   Companies list - New: {companies_saved}, Updated: {companies_updated}, Skipped: {companies_skipped}")
        logger.info(f"   Illiquid maintenance suspension list - New: {illiquid_saved}, Updated: {illiquid_updated}, Skipped: {illiquid_skipped}")
        logger.info(f"   Trading code list - New: {trading_code_saved}, Updated: {trading_code_updated}, Skipped: {trading_code_skipped}")
        logger.info(f"   Securities types - New: {securities_types_saved}, Updated: {securities_types_updated}, Skipped: {securities_types_skipped}")
        logger.info(f"   Public holdings indices - New: {public_holdings_saved}, Updated: {public_holdings_updated}, Skipped: {public_holdings_skipped}")
        logger.info(f"   Expected changes IANS float - New: {expected_changes_saved}, Updated: {expected_changes_updated}, Skipped: {expected_changes_skipped}")
        logger.info(f"   Expected changes weight factor - New: {expected_changes_weight_saved}, Updated: {expected_changes_weight_updated}, Skipped: {expected_changes_weight_skipped}")
        logger.info(f"   Index components extended - New: {index_components_extended_saved}, Updated: {index_components_extended_updated}, Skipped: {index_components_extended_skipped}")
        logger.info(f"   Parameters update schedule - New: {parameters_update_schedule_saved}, Updated: {parameters_update_schedule_updated}, Skipped: {parameters_update_schedule_skipped}")
        logger.info(f"   Indices constituents update - New: {indices_constituents_update_saved}, Updated: {indices_constituents_update_updated}, Skipped: {indices_constituents_update_skipped}")
        logger.info(f"   Capital listed for trading EOD - New: {capital_listed_eod_saved}, Updated: {capital_listed_eod_updated}, Skipped: {capital_listed_eod_skipped}")
        logger.info(f"   Constituents update lists - New: {constituents_update_lists_saved}, Updated: {constituents_update_lists_updated}, Skipped: {constituents_update_lists_skipped}")
        logger.info(f"   Bond data - New: {bond_data_saved}, Updated: {bond_data_updated}, Skipped: {bond_data_skipped}")
        logger.info(f"   Universe constituents update - New: {universe_constituents_saved}, Updated: {universe_constituents_updated}, Skipped: {universe_constituents_skipped}")
        logger.info(f"   Update types - New: {update_types_saved}, Updated: {update_types_updated}, Skipped: {update_types_skipped}")
        logger.info(f"   Merge to core - Trade: {trade_inserted} inserted, {trade_updated_merge} updated")
        logger.info(f"   Merge to core - EX codes: {ex_inserted} inserted, {ex_updated} updated")
        logger.info(f"   Merge to core - Traded securities: {traded_sec_inserted} inserted, {traded_sec_updated_merge} updated")
        logger.info(f"   Merge to core - Delisted securities: {delisted_sec_inserted} inserted, {delisted_sec_updated_merge} updated")
        logger.info(f"   Merge to core - Companies: {companies_inserted} inserted, {companies_updated_merge} updated")
        logger.info(f"   Merge to core - Illiquid: {illiquid_inserted} inserted, {illiquid_updated_merge} updated")
        logger.info(f"   Merge to core - Trading code: {trading_code_inserted} inserted, {trading_code_updated_merge} updated")
        logger.info(f"   Merge to core - Securities types: {securities_types_inserted} inserted, {securities_types_updated_merge} updated")
        logger.info(f"   Merge to core - Public holdings indices: {public_holdings_inserted} inserted, {public_holdings_updated_merge} updated")
        logger.info(f"   Merge to core - Expected changes IANS float: {expected_changes_inserted} inserted, {expected_changes_updated_merge} updated")
        logger.info(f"   Merge to core - Expected changes weight factor: {expected_changes_weight_inserted} inserted, {expected_changes_weight_updated_merge} updated")
        logger.info(f"   Merge to core - Index components extended: {index_components_extended_inserted} inserted, {index_components_extended_updated_merge} updated")
        logger.info(f"   Merge to core - Parameters update schedule: {parameters_update_schedule_inserted} inserted, {parameters_update_schedule_updated_merge} updated")
        logger.info(f"   Merge to core - Indices constituents update: {indices_constituents_update_inserted} inserted, {indices_constituents_update_updated_merge} updated")
        logger.info(f"   Merge to core - Capital listed for trading EOD: {capital_listed_eod_inserted} inserted, {capital_listed_eod_updated_merge} updated")
        logger.info(f"   Merge to core - Constituents update lists: {constituents_update_lists_inserted} inserted, {constituents_update_lists_updated_merge} updated")
        logger.info(f"   Merge to core - Bond data: {bond_data_inserted} inserted, {bond_data_updated_merge} updated")
        logger.info(f"   Merge to core - Universe constituents update: {universe_constituents_inserted} inserted, {universe_constituents_updated_merge} updated")
        logger.info(f"   Merge to core - Update types: {update_types_inserted} inserted, {update_types_updated_merge} updated")
        logger.info(f"   Run time: {duration:.2f} seconds")
        logger.info("=" * 70)

        return True

    except Exception as e:
        logger.error(f"\nError in daily run: {e}")
        logger.exception("Full error details:")
        return False




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract TASE EOD data for a specific date')
    parser.add_argument(
        '--date',
        type=str,
        help='Date to extract data for (format: YYYY-MM-DD). If not provided, defaults to November 4, 2025.',
        default=None
    )

    args = parser.parse_args()

    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"Invalid date format: {args.date}. Expected format: YYYY-MM-DD")
            exit(1)

    success = main(target_date)
    exit(0 if success else 1)