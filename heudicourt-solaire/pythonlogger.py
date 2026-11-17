#!/usr/bin/python3
"""Shelly EM + temperature logger.

Usage (same arguments as before, so /etc/rc.local does not need to change):
    pythonlogger.py <database> <shelly_ip> <interval_s> <temp_repetitions>

Example:
    pythonlogger.py /home/pi/RPI-Heudicourt/database/logdata.db 192.168.1.55 60 15
"""

import argparse
import logging
import sys

from python_functions import write_database


def main():
    parser = argparse.ArgumentParser(description='Shelly EM Logger')
    parser.add_argument('database', help='Path to the SQLite database file')
    parser.add_argument('ip', help='IP address of the Shelly device')
    parser.add_argument('interval', type=int, help='Polling interval in seconds')
    parser.add_argument('temp_repetitions', type=int,
                        help='Number of polling iterations between two temperature readings')
    args = parser.parse_args()

    if args.interval < 1 or args.temp_repetitions < 1:
        parser.error('interval and temp_repetitions must be >= 1')

    # Logs go to stdout: rc.local redirects them to the log file, systemd to journald
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s')

    write_database(args.database, args.ip, args.interval, args.temp_repetitions)


if __name__ == "__main__":
    main()