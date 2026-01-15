"""
Scheduler for daily run - runs main() function at configurable intervals
"""

import logging
import os
import time
import argparse
import schedule
import threading
from datetime import datetime
from main_daily import main
from heartbeat import update_heartbeat

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Default intervals in minutes (can be overridden by environment variables or command line arguments)
DEFAULT_INTERVAL_RUNNING_MINUTES = 2
DEFAULT_INTERVAL_HEARTBEAT_MINUTES = 1


def run_daily_extraction():
    """
    Wrapper function to run the daily extraction
    """
    logger.info("=" * 70)
    logger.info(f"Scheduled run started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    try:
        # Run main() with None to use today's date
        success = main(target_date=None)
        
        if success:
            logger.info(f"Scheduled run completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            logger.error(f"Scheduled run failed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        logger.info("=" * 70)
        return success
        
    except Exception as e:
        logger.error(f"Error in scheduled run: {e}")
        logger.exception("Full error details:")
        return False


def heartbeat_worker(interval_heartbeat_minutes: int, stop_event: threading.Event):
    """
    Worker thread for heartbeat updates - runs independently of main logic
    Args:
        interval_heartbeat_minutes: Interval in minutes between heartbeat updates
        stop_event: Event to signal thread to stop
    """
    logger.info(f"Heartbeat thread started - will update every {interval_heartbeat_minutes} minutes")
    
    # Update initial heartbeat
    update_heartbeat()
    
    interval_seconds = interval_heartbeat_minutes * 60
    
    while not stop_event.is_set():
        try:
            # Wait for the interval or until stop event is set
            if stop_event.wait(timeout=interval_seconds):
                # Stop event was set, exit loop
                break
            
            # Update heartbeat
            update_heartbeat()
            logger.debug(f"Heartbeat updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"Error in heartbeat thread: {e}")
            logger.exception("Full error details:")
            # Continue running even if there's an error
            continue
    
    # Final heartbeat update before thread exits
    update_heartbeat()
    logger.info("Heartbeat thread stopped")


def start_scheduler(interval_running_minutes: int, interval_heartbeat_minutes: int, run_immediately: bool = True):
    """
    Start the scheduler to run main() at specified intervals
    Args:
        interval_running_minutes: Interval in minutes between main() runs (required argument).
        interval_heartbeat_minutes: Interval in minutes between heartbeat updates (required argument).
        run_immediately: Whether to run main() immediately on start (default: True).
    """
    logger.info("=" * 70)
    logger.info("Scheduler Configuration:")
    logger.info(f"  - Running interval: {interval_running_minutes} minutes")
    logger.info(f"  - Heartbeat interval: {interval_heartbeat_minutes} minutes")
    logger.info(f"  - Run immediately on start: {run_immediately}")
    logger.info(f"Scheduler started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    # Create stop event for heartbeat thread
    stop_event = threading.Event()
    
    # Start heartbeat thread (runs independently)
    heartbeat_thread = threading.Thread(
        target=heartbeat_worker,
        args=(interval_heartbeat_minutes, stop_event),
        name="HeartbeatThread",
        daemon=False  # Not a daemon thread - will keep running until explicitly stopped
    )
    heartbeat_thread.start()
    logger.info("Heartbeat thread started in background")
    
    # Schedule the job to run at specified interval
    schedule.every(interval_running_minutes).minutes.do(run_daily_extraction)
    
    # Run immediately on start if requested
    if run_immediately:
        logger.info("Running initial extraction...")
        run_daily_extraction()
    
    # Keep the scheduler running
    logger.info("Scheduler is now running. Press Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            logger.info(f"Scheduler is running - waiting for next job. Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(60)  # Check every minute if there's a job to run
            
    except KeyboardInterrupt:
        logger.info("\nScheduler stopped by user")
        logger.info(f"Scheduler stopped at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    finally:
        # Signal heartbeat thread to stop
        logger.info("Stopping heartbeat thread...")
        stop_event.set()
        
        # Wait for heartbeat thread to finish (with timeout)
        heartbeat_thread.join(timeout=5)
        if heartbeat_thread.is_alive():
            logger.warning("Heartbeat thread did not stop gracefully within timeout")
        else:
            logger.info("Heartbeat thread stopped successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Scheduler for daily run with configurable intervals',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run every 2 hours, heartbeat every 1 minute
  python3 scheduler.py --interval-running 120 --interval-heartbeat 1
  
  # Run every 30 minutes, heartbeat every 5 minutes, skip initial run
  python3 scheduler.py --interval-running 30 --interval-heartbeat 5 --no-run-immediately
  
  # Use environment variables
  export SCHEDULER_INTERVAL_RUNNING=60
  export SCHEDULER_INTERVAL_HEARTBEAT=2
  python3 scheduler.py
        """
    )
    
    parser.add_argument(
        '--interval-running',
        type=int,
        help=f'Interval in minutes between main() runs (default: {DEFAULT_INTERVAL_RUNNING_MINUTES} or from SCHEDULER_INTERVAL_RUNNING env var)',
        default=None
    )
    
    parser.add_argument(
        '--interval-heartbeat',
        type=int,
        help=f'Interval in minutes between heartbeat updates (default: {DEFAULT_INTERVAL_HEARTBEAT_MINUTES} or from SCHEDULER_INTERVAL_HEARTBEAT env var)',
        default=None
    )
    
    parser.add_argument(
        '--no-run-immediately',
        action='store_true',
        help='Skip running main() immediately on start (default: runs immediately)'
    )
    
    args = parser.parse_args()
    
    # Get interval_running from argument, environment variable, or default
    interval_running = args.interval_running
    if interval_running is None:
        interval_running = int(os.getenv('SCHEDULER_INTERVAL_RUNNING', DEFAULT_INTERVAL_RUNNING_MINUTES))
    
    # Get interval_heartbeat from argument, environment variable, or default
    interval_heartbeat = args.interval_heartbeat
    if interval_heartbeat is None:
        interval_heartbeat = int(os.getenv('SCHEDULER_INTERVAL_HEARTBEAT', DEFAULT_INTERVAL_HEARTBEAT_MINUTES))
    
    # Validate intervals
    if interval_running < 1:
        logger.error(f"Invalid interval_running: {interval_running}. Must be at least 1 minute.")
        exit(1)
    
    if interval_heartbeat < 1:
        logger.error(f"Invalid interval_heartbeat: {interval_heartbeat}. Must be at least 1 minute.")
        exit(1)
    
    if interval_heartbeat > interval_running:
        logger.warning(f"Warning: interval_heartbeat ({interval_heartbeat}) is greater than interval_running ({interval_running}). "
                      f"This may cause heartbeat to update less frequently than expected.")
    
    start_scheduler(
        interval_running_minutes=interval_running,
        interval_heartbeat_minutes=interval_heartbeat,
        run_immediately=not args.no_run_immediately
    )

