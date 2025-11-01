#!/usr/bin/python3

# import requests
# import sqlite3
# import time
# import datetime

# ip_address = '192.168.1.55'
# db_file = '/home/pi/database/logdata.db'

import argparse
from python_functions import *


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Shelly EM Logger")
    parser.add_argument("database", help="Path to the SQLite database file")
    parser.add_argument("ip", help="IP address of the Shelly device")
    parser.add_argument("interval", help="Polling interval")
    args = parser.parse_args()

    write_database(args.database, args.ip, args.interval)






## Turn OFF relay 0
##requests.get(f"http://{ip}/relay/0?turn=off")

#import subprocess

#result = subprocess.run(['ls', '-al'], capture_output=True, text=True)
#output = result.stdout
#print (output)
