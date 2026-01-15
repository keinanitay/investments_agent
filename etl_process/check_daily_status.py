"""
Check the status of daily runs
Verifies that the daily extraction process ran successfully
"""

import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

# Colors for terminal output (works on most terminals)
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def check_log_file(log_path, days_back=7):
    """
    Check the daily_run.log file for recent successful runs
    """
    if not os.path.exists(log_path):
        return {
            'found': False,
            'last_run': None,
            'success': False,
            'message': f"Log file not found: {log_path}"
        }

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Look for successful completion messages
        success_patterns = [
            "Daily run completed successfully",
            "Run time:",
            "Summary:"
        ]

        # Look for error messages
        error_patterns = [
            "Error in daily run",
            "Exception",
            "Traceback",
            "ERROR"
        ]

        last_success_date = None
        last_error_date = None
        recent_errors = []

        # Check last N days
        check_date = date.today()
        for i in range(days_back):
            check_date_str = check_date.strftime('%Y-%m-%d')

            # Check if there's a successful run for this date
            date_found = False
            success_found = False
            error_found = False

            for line in lines:
                if check_date_str in line:
                    date_found = True
                    if any(pattern in line for pattern in success_patterns):
                        success_found = True
                    if any(pattern in line for pattern in error_patterns):
                        error_found = True
                        recent_errors.append(f"{check_date_str}: {line.strip()}")

            if date_found:
                if success_found and not error_found:
                    if last_success_date is None:
                        last_success_date = check_date
                elif error_found:
                    if last_error_date is None:
                        last_error_date = check_date

            check_date -= timedelta(days=1)

        # Get the most recent log entry
        last_line = lines[-1].strip() if lines else ""

        return {
            'found': True,
            'last_run': last_success_date,
            'last_error': last_error_date,
            'success': last_success_date is not None and (last_error_date is None or last_success_date > last_error_date),
            'recent_errors': recent_errors[:5],  # Last 5 errors
            'last_log_line': last_line
        }

    except Exception as e:
        return {
            'found': True,
            'last_run': None,
            'success': False,
            'message': f"Error reading log file: {e}"
        }

def check_cron_log(cron_log_path):
    """
    Check the cron_daily.log file for execution records
    """
    if not os.path.exists(cron_log_path):
        return {
            'found': False,
            'last_execution': None,
            'message': f"Cron log file not found: {cron_log_path}"
        }

    try:
        with open(cron_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if not lines:
            return {
                'found': True,
                'last_execution': None,
                'message': "Cron log file is empty"
            }

        # Get last execution
        last_line = lines[-1].strip()

        return {
            'found': True,
            'last_execution': last_line,
            'total_executions': len(lines)
        }

    except Exception as e:
        return {
            'found': True,
            'last_execution': None,
            'message': f"Error reading cron log: {e}"
        }

def check_database_connection():
    """
    Check if we can connect to the database
    """
    try:
        from database import get_database, close_connection
        
        db = get_database()
        # Test connection by running a simple command
        db.command('ping')
        
        return {
            'success': True,
            'message': "Database connection successful"
        }
    except Exception as e:
        return {
            'success': False,
            'message': f"Database connection failed: {e}"
        }
    finally:
        try:
            close_connection()
        except:
            pass

def main():
    """Main function to check daily run status"""

    # Get project directory
    project_dir = Path(__file__).parent
    daily_log = project_dir / "daily_run.log"
    cron_log = project_dir / "cron_daily.log"

    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}TASE Daily Run Status Check{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")

    # Check daily_run.log
    print(f"{Colors.BOLD}Checking daily_run.log...{Colors.RESET}")
    log_status = check_log_file(daily_log, days_back=7)

    if not log_status['found']:
        print(f"{Colors.RED}✗ {log_status['message']}{Colors.RESET}\n")
    else:
        if log_status['success']:
            if log_status['last_run']:
                days_ago = (date.today() - log_status['last_run']).days
                if days_ago == 0:
                    print(f"{Colors.GREEN}✓ Last successful run: Today ({log_status['last_run']}){Colors.RESET}")
                elif days_ago == 1:
                    print(f"{Colors.YELLOW}⚠ Last successful run: Yesterday ({log_status['last_run']}){Colors.RESET}")
                else:
                    print(f"{Colors.YELLOW}⚠ Last successful run: {days_ago} days ago ({log_status['last_run']}){Colors.RESET}")
            else:
                print(f"{Colors.RED}✗ No successful runs found in the last 7 days{Colors.RESET}")

            if log_status['last_error']:
                print(f"{Colors.YELLOW}⚠ Last error: {log_status['last_error']}{Colors.RESET}")

            if log_status['recent_errors']:
                print(f"{Colors.RED}Recent errors:{Colors.RESET}")
                for error in log_status['recent_errors']:
                    print(f"  {Colors.RED}- {error}{Colors.RESET}")
        else:
            print(f"{Colors.RED}✗ {log_status.get('message', 'No successful runs found')}{Colors.RESET}")

        if log_status.get('last_log_line'):
            print(f"{Colors.BLUE}Last log entry: {log_status['last_log_line'][:100]}...{Colors.RESET}")

    print()

    # Check cron_daily.log
    print(f"{Colors.BOLD}Checking cron_daily.log...{Colors.RESET}")
    cron_status = check_cron_log(cron_log)

    if not cron_status['found']:
        print(f"{Colors.YELLOW}⚠ {cron_status['message']}{Colors.RESET}\n")
    else:
        if cron_status.get('last_execution'):
            print(f"{Colors.GREEN}✓ Last cron execution: {cron_status['last_execution']}{Colors.RESET}")
            if cron_status.get('total_executions'):
                print(f"{Colors.BLUE}Total executions logged: {cron_status['total_executions']}{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}⚠ {cron_status.get('message', 'No execution records found')}{Colors.RESET}")

    print()

    # Check database connection
    print(f"{Colors.BOLD}Checking database connection...{Colors.RESET}")
    db_status = check_database_connection()

    if db_status['success']:
        print(f"{Colors.GREEN}✓ {db_status['message']}{Colors.RESET}")
    else:
        print(f"{Colors.RED}✗ {db_status['message']}{Colors.RESET}")

    print()
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")

    # Overall status
    overall_success = (
        log_status.get('success', False) and
        db_status.get('success', False)
    )

    if overall_success:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ Overall Status: HEALTHY{Colors.RESET}")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Overall Status: ISSUES DETECTED{Colors.RESET}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
