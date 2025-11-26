#!/usr/bin/env python3
# Location: /scripts/run_monitor.py
# Purpose: Launcher script for ICE real-time monitoring daemon
# Why: Provide easy way to start/stop/status the monitoring service
# Relevant Files: real_time_monitor.py, monitor.json

"""
ICE Real-Time Monitor Launcher

Usage:
    python scripts/run_monitor.py start    # Start monitor daemon
    python scripts/run_monitor.py stop     # Stop monitor daemon
    python scripts/run_monitor.py status   # Check monitor status
    python scripts/run_monitor.py test     # Run in test mode (foreground)
"""

import os
import sys
import asyncio
import signal
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ice_core.real_time_monitor import RealTimeMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# PID file for daemon management
PID_FILE = project_root / 'logs' / 'monitor.pid'


def start_monitor(config_path: str = None, test_mode: bool = False):
    """Start the real-time monitor"""

    if not test_mode and PID_FILE.exists():
        print(f"Monitor already running (PID file exists: {PID_FILE})")
        return 1

    # Load configuration
    if not config_path:
        config_path = project_root / 'config' / 'monitor.json'

    if not Path(config_path).exists():
        print(f"Configuration file not found: {config_path}")
        return 1

    print(f"Starting ICE Real-Time Monitor...")
    print(f"Configuration: {config_path}")
    print(f"Log file: logs/monitor.log")

    # Create monitor instance
    monitor = RealTimeMonitor(str(config_path))

    # Signal handlers
    def signal_handler(sig, frame):
        print("\nShutting down monitor...")
        asyncio.create_task(monitor.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Save PID if not in test mode
    if not test_mode:
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))

    try:
        # Run monitor
        asyncio.run(monitor.start())
    except KeyboardInterrupt:
        print("\nMonitor interrupted by user")
    finally:
        # Clean up PID file
        if not test_mode and PID_FILE.exists():
            PID_FILE.unlink()

    return 0


def stop_monitor():
    """Stop the running monitor daemon"""

    if not PID_FILE.exists():
        print("Monitor is not running (no PID file found)")
        return 1

    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())

        # Send termination signal
        os.kill(pid, signal.SIGTERM)
        print(f"Sent termination signal to monitor (PID: {pid})")

        # Clean up PID file
        PID_FILE.unlink()
        return 0

    except ProcessLookupError:
        print(f"Monitor process not found (stale PID file)")
        PID_FILE.unlink()
        return 1
    except Exception as e:
        print(f"Error stopping monitor: {e}")
        return 1


def check_status():
    """Check if monitor is running"""

    if not PID_FILE.exists():
        print("Monitor Status: STOPPED")
        return 0

    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())

        # Check if process exists
        os.kill(pid, 0)
        print(f"Monitor Status: RUNNING (PID: {pid})")

        # Show configuration summary
        config_path = project_root / 'config' / 'monitor.json'
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                print(f"Portfolio Tickers: {', '.join(config.get('portfolio_tickers', []))}")
                print(f"News Interval: {config.get('news_interval', 300)}s")
                print(f"SEC Interval: {config.get('sec_interval', 900)}s")

        return 0

    except ProcessLookupError:
        print("Monitor Status: STOPPED (stale PID file)")
        PID_FILE.unlink()
        return 1


def run_test_mode():
    """Run monitor in test/debug mode (foreground)"""

    print("=" * 60)
    print("ICE REAL-TIME MONITOR - TEST MODE")
    print("=" * 60)
    print("Running in foreground with debug output...")
    print("Press Ctrl+C to stop")
    print("-" * 60)

    # Set debug logging
    logging.getLogger().setLevel(logging.DEBUG)

    # Create test configuration
    test_config = {
        'portfolio_tickers': ['NVDA', 'AAPL', 'MSFT'],
        'sector_exposures': {'AI': 0.3, 'Cloud': 0.2},
        'news_interval': 60,  # 1 minute for testing
        'sec_interval': 120,  # 2 minutes for testing
        'delivery': {
            'email_enabled': False,
            'slack_enabled': False,
            'log_enabled': True
        }
    }

    # Save test config
    test_config_path = project_root / 'config' / 'monitor_test.json'
    with open(test_config_path, 'w') as f:
        json.dump(test_config, f, indent=2)

    # Start monitor
    return start_monitor(str(test_config_path), test_mode=True)


def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(
        description='ICE Real-Time Monitor Launcher',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'command',
        choices=['start', 'stop', 'status', 'test'],
        help='Command to execute'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file (default: config/monitor.json)'
    )

    args = parser.parse_args()

    # Execute command
    if args.command == 'start':
        return start_monitor(args.config)
    elif args.command == 'stop':
        return stop_monitor()
    elif args.command == 'status':
        return check_status()
    elif args.command == 'test':
        return run_test_mode()


if __name__ == "__main__":
    sys.exit(main())