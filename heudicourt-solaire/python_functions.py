#!/usr/bin/python3

import sqlite3
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from tabulate import tabulate
import requests
import sqlite3
import time

import re
import subprocess


def read_temperatures ():

        lst_temp = []
        r_temp = re.compile('t=([0-9]+)')
        dct_sensors = {'salon': '28-0000067c14c7',
                        'cour': '28-0000050b221b',
                        'grenier': '28-15dccf1964ff',
                        'cellier': '28-6cb8cf1964ff',
                        'chaufferie': '28-1806ce1964ff'}
        bus_path = '/home/francis/sys-bus-w1-devices/'

        address = bus_path + dct_sensors['salon'] + '/w1_slave'
        stdout = subprocess.run(['cat', address], capture_output=True, text=True).stdout

        for key, value in dct_sensors.items():

                address = '/home/francis/sys-bus-w1-devices/' + value + '/w1_slave'
                stdout = subprocess.run(['cat', address], capture_output=True, text=True).stdout

                sens_out = r_temp.findall(stdout)
                if len(sens_out) > 0:
                        if sens_out[0].isdigit():
                                lst_temp.append(int(sens_out[0])/1000)
                        else:
                                lst_temp.append(None)
                else:
                        lst_temp.append(None)

        return dct_sensors, lst_temp


def read_gpio(gpio_no=17):

    gpio_value = None
    r_gpio = re.compile('([0-9])\n')
    gpio_path = '/home/francis/sys-class-gpio-gpio' + str(gpio_no) + '/'

    address = gpio_path + '/value'
    stdout = subprocess.run(['cat', address], capture_output=True, text=True).stdout
    
    gpio_out = r_gpio.findall(stdout)

    if len(gpio_out) > 0:
        if gpio_out[0].isdigit():
                gpio_value = int(gpio_out[0])

    return gpio_value

 
def write_database (db_file, ip_shelly, polling_interval='60', temp_repetitions='2'):
        try:
                while True:

                        try:

                                timestamp = datetime.datetime.now().isoformat()
                                print('Timestamp:', timestamp)

                                # 3 attempts
                                for attempt in range(3):
                                        try:
                                                response = requests.get(f'http://{ip_shelly}/status', timeout=5)
                                                status = response.json()
                                                break
                                        except requests.exceptions.RequestException:
                                                time.sleep(2)
                                else:
                                        print ('Failed after 3 retries')

                                # Powers

                                device_cons = status['emeters'][0]
                                device_prod = status['emeters'][1]

                                power_cons = device_cons['power']
                                voltage_cons = device_cons['voltage']
                                power_prod = device_prod['power']
                                voltage_cons = device_prod['voltage']

                                print('Power consumption:', power_cons, 'W')
                                print('Power production:', power_prod, 'W')

                                conn = sqlite3.connect(db_file, timeout=60)
                                conn.execute("PRAGMA journal_mode=WAL;")
                                c = conn.cursor()

                                for device in [0, 1]:

                                        table_name = 'emeters' + str(device)

                                        sql = 'CREATE TABLE IF NOT EXISTS ' + table_name + \
                                                ' (timestamp DATETIME, power REAL,' + \
                                                ' reactive REAL, voltage REAL, is_valid INT,' + \
                                                ' total REAL, total_returned REAL);'
                                        c.execute(sql)

                                        sql = 'INSERT INTO ' + table_name + ' (timestamp, power, reactive, voltage, is_valid, total, total_returned)' + \
                                                ' VALUES (?, ?, ?, ?, ?, ?, ?);'
                                        power = status['emeters'][device]['power']
                                        reactive = status['emeters'][device]['reactive']
                                        voltage = status['emeters'][device]['voltage']
                                        is_valid = status['emeters'][device]['is_valid']
                                        is_valid_int = 1 if is_valid else 0
                                        total = status['emeters'][device]['total']
                                        total_returned = status['emeters'][device]['total_returned']
                                        c.execute(sql, (timestamp, power, reactive, voltage, is_valid_int, total, total_returned))

                                # Relays

                                relay_ison = status['relays'][0]['ison']
                                print('Relay status:', relay_ison)

                                sql = 'CREATE TABLE IF NOT EXISTS relay (timestamp DATETIME, ison INT);'
                                c.execute(sql)

                                sql = 'INSERT INTO relay (timestamp, ison)' + \
                                        ' VALUES (?, ?);'
                                ison_int = 1 if relay_ison else 0
                                c.execute(sql, (timestamp, ison_int))

                                # After n repetitions, log additionally temperatures & gpio
                                counter_repetition =+ 1

                                if counter_repetition == int(temp_repetitions):

                                        # Temperatures
                                        db_sensors, db_temp = read_temperatures()
                                        print('Temperatures:', db_temp)                                        

                                        db_temp.insert(0, timestamp)                                        

                                        sql = 'CREATE TABLE IF NOT EXISTS temperatures' + \
                                                ' (timestamp DATETIME,' + \
                                                ' temp_1 REAL, temp_2 REAL, temp_3 REAL, temp_4 REAL, temp_5 REAL);'
                                        c.execute(sql)

                                        sql = 'INSERT INTO temperatures (timestamp, temp_1, temp_2, temp_3, temp_4, temp_5)' + \
                                                ' VALUES (?, ?, ?, ?, ?, ?);'
                                        c.execute(sql, db_temp)

                                        # GPIO
                                        db_gpio = [read_gpio(17)]
                                        print('GPIO:', db_gpio)

                                        db_gpio.insert(0, timestamp)

                                        sql = 'CREATE TABLE IF NOT EXISTS gpio' + \
                                                ' (timestamp DATETIME, gpio_value INT);'
                                        c.execute(sql)

                                        sql = 'INSERT INTO gpio (timestamp, gpio_value)' + \
                                                ' VALUES (?, ?);'
                                        c.execute(sql, db_gpio)

                                        # Reset counter
                                        counter_repetition = 0

                                # Database
                                conn.commit()                
                                conn.close()

                                time.sleep(int(polling_interval))

                        except requests.exceptions.RequestException as e:
                                print ('Shelly unreachable:', e)
                                counter_occurence = 0

        except KeyboardInterrupt:
                print ('Logging interrupted.')

        finally:
                print ('SQLite connection closed.')
                conn.close()


def read_database (db_file):

        # Database
        conn = sqlite3.connect (db_file)
        c = conn.cursor()

        sql = """CREATE VIEW IF NOT EXISTS vwPlot AS
                SELECT em0.[timestamp],
                        em0.[power] as 'power_0',
                        em1.[power] as 'power_1',
                        rel.[ison] as 'relay_state'
                FROM emeters0 AS em0
                        INNER JOIN emeters1 AS em1 ON em0.[timestamp] = em1.[timestamp]
                                INNER JOIN relay AS rel ON em0.[timestamp] = rel.[timestamp]
                WHERE em0.[timestamp] >= datetime('now', '-2 day');"""
        c.execute(sql)

        sql = """SELECT [timestamp], [power_0], [power_1], [relay_state]
                FROM vwPlot ORDER BY [timestamp]"""
        c.execute(sql)
        rows = c.fetchall()
        conn.close()

        return rows


def plot_logdata (db_file, png_file):

        rows = read_database(db_file)

        # Reduction : keep every 4th point
        idx = range(0, len(rows), 4)
        rows_red = [rows[i] for i in idx]

        time = [datetime.datetime.fromisoformat(r[0]) for r in rows_red]
        power_0 = [r[1] for r in rows_red]
        power_1 = [-r[2] for r in rows_red]
        relay_state = [r[3] for r in rows_red]

        # Graphics
        fig, ax1 = plt.subplots(figsize=(10, 4))
        ax2 = ax1.twinx()

        ax1.plot(time, power_0, label='Consommation', color='b')
        ax1.plot(time, power_1, label='Production', color='r')
        ax2.plot(time, relay_state, label='Relais', color='g')

        plt.xlabel('Date')
        plt.ylabel('Puissance (W)')
        plt.title('')

        ax2.set_yticks([0, 1])
        ax2.set_ylim([0, 10])

        ax1.grid(True)

        fig.legend(loc='upper left')
        fig.tight_layout()

        fig.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b-%d %H:%M'))
        plt.gcf().autofmt_xdate()
        fig.savefig(png_file)


def display_logdata (db_file):

        rows = read_database(db_file)

        # 360 last lines (6 hours)
        rows1 = rows[-360:]

        print(tabulate(rows1[::-1], headers=["Date / Heure", "Conso.", "Prod.", "Relais"], tablefmt="psql"))

