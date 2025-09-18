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




# try:
#     while True:

#         try:

#             timestamp = datetime.datetime.now().isoformat()
#             print('Timestamp:', timestamp)

#             # 3 attempts
#             for attempt in range(3):
#                 try:
#                     response = requests.get(f'http://{ip_address}/status', timeout=5)
#                     status = response.json()
#                     break
#                 except requests.exceptions.RequestException:
#                     time.sleep(2)
#             else:
#                 print ('Failed after 3 retries')

#             # Powers

#             device_cons = status['emeters'][0]
#             device_prod = status['emeters'][1]

#             power_cons = device_cons['power']
#             voltage_cons = device_cons['voltage']
#             power_prod = device_prod['power']
#             voltage_cons = device_prod['voltage']

#             print('Power consumption:', power_cons, 'W')
#             print('Power production:', power_prod, 'W')

#             conn = sqlite3.connect(db_file)
#             c = conn.cursor()

#             for device in [0, 1]:

#                 table_name = 'emeters' + str(device)

#                 sql = 'CREATE TABLE IF NOT EXISTS ' + table_name + \
#                         ' (timestamp DATETIME, power REAL,' + \
#                         ' reactive REAL, voltage REAL, is_valid INT,' + \
#                         ' total REAL, total_returned REAL);'
#                 c.execute(sql)

#                 sql = 'INSERT INTO ' + table_name + ' (timestamp, power, reactive, voltage, is_valid, total, total_returned)' + \
#                         ' VALUES (?, ?, ?, ?, ?, ?, ?);'
#                 power = status['emeters'][device]['power']
#                 reactive = status['emeters'][device]['reactive']
#                 voltage = status['emeters'][device]['voltage']
#                 is_valid = status['emeters'][device]['is_valid']
#                 is_valid_int = 1 if is_valid else 0
#                 total = status['emeters'][device]['total']
#                 total_returned = status['emeters'][device]['total_returned']
#                 c.execute(sql, (timestamp, power, reactive, voltage, is_valid_int, total, total_returned))

#             # Relays

#             relay_ison = status['relays'][0]['ison']
#             print('Relay status:', relay_ison)

#             sql = 'CREATE TABLE IF NOT EXISTS relay (timestamp DATETIME, ison INT);'
#             c.execute(sql)

#             sql = 'INSERT INTO relay (timestamp, ison)' + \
#                     ' VALUES (?, ?);'
#             ison_int = 1 if relay_ison else 0
#             c.execute(sql, (timestamp, ison_int))

#             # Database
#             conn.commit()                
#             conn.close()

#             time.sleep(60)

#         except requests.exceptions.RequestException as e:
#             print ('Shelly unreachable:', e)
            
# except KeyboardInterrupt:
#         print ('Logging interrupted.')

# finally:
#         print ('SQLite connection closed.')
#         conn.close()




## Turn OFF relay 0
##requests.get(f"http://{ip}/relay/0?turn=off")

#import subprocess

#result = subprocess.run(['ls', '-al'], capture_output=True, text=True)
#output = result.stdout
#print (output)
