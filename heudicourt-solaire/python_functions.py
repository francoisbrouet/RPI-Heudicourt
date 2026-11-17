#!/usr/bin/python3
"""Helper functions for the Heudicourt solar / temperature logger.

Logging side (used by pythonlogger.py):
    write_database(), read_temperatures(), read_gpio()

Display side (used by other scripts / the web server):
    read_database(), plot_logdata(), display_logdata()
    -> matplotlib and tabulate are imported lazily, so the logger itself
       does not need them (faster start and lower memory on a Pi 1).
"""

import datetime
import logging
import os
import re
import signal
import sqlite3
import threading
import time

import requests

log = logging.getLogger("pythonlogger")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# 1-Wire bus and GPIO paths. The defaults are the real sysfs paths.
# If you really use copies elsewhere (e.g. /home/francis/sys-bus-w1-devices/),
# set the environment variables W1_BUS_PATH / GPIO_VALUE_PATH, or edit here.
W1_BUS_PATH = os.environ.get('W1_BUS_PATH', '/sys/bus/w1/devices/')
GPIO_VALUE_PATH = os.environ.get('GPIO_VALUE_PATH', '/sys/class/gpio/gpio{}/value')

# Order matters: it maps to temp_1 .. temp_5 in the 'temperatures' table.
SENSORS = {
    'salon': '28-0000067c14c7',
    'cour': '28-0000050b221b',
    'grenier': '28-15dccf1964ff',
    'cellier': '28-6cb8cf1964ff',
    'chaufferie': '28-1806ce1964ff',
}

R_TEMP = re.compile(r't=(-?\d+)')

SHELLY_RETRIES = 3
SHELLY_TIMEOUT = 5          # seconds
SHELLY_RETRY_DELAY = 2      # seconds

# Set by SIGTERM/SIGINT so the loop can stop cleanly (systemd, Ctrl-C)
_stop_event = threading.Event()


# ---------------------------------------------------------------------------
# Sensors
# ---------------------------------------------------------------------------

def read_ds18b20(sensor_id):
    """Return the temperature in degrees C, or None if the reading is invalid."""
    path = os.path.join(W1_BUS_PATH, sensor_id, 'w1_slave')
    try:
        with open(path) as f:
            lines = f.read().splitlines()
    except OSError as e:
        log.warning('Cannot read sensor %s: %s', sensor_id, e)
        return None

    # First line ends with YES when the CRC is valid
    if len(lines) < 2 or not lines[0].strip().endswith('YES'):
        log.warning('Sensor %s: invalid CRC', sensor_id)
        return None

    m = R_TEMP.search(lines[1])
    if not m:
        return None

    value = int(m.group(1)) / 1000
    if value == 85.0:       # power-on reset value of the DS18B20, not a real reading
        log.warning('Sensor %s: 85 C power-on value ignored', sensor_id)
        return None
    return value


def read_temperatures():
    """Return (dict of sensors, list of temperatures in the same order)."""
    return SENSORS, [read_ds18b20(sensor_id) for sensor_id in SENSORS.values()]


def read_gpio(gpio_no=17):
    """Return the GPIO value (0/1) or None if it cannot be read."""
    path = GPIO_VALUE_PATH.format(gpio_no)
    try:
        with open(path) as f:
            return int(f.read().strip())
    except (OSError, ValueError) as e:
        log.warning('Cannot read GPIO %s: %s', gpio_no, e)
        return None


# ---------------------------------------------------------------------------
# Shelly
# ---------------------------------------------------------------------------

def get_shelly_status(ip_shelly):
    """Return the Shelly /status JSON, or None after SHELLY_RETRIES failures."""
    for attempt in range(1, SHELLY_RETRIES + 1):
        try:
            response = requests.get(f'http://{ip_shelly}/status', timeout=SHELLY_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as e:
            log.warning('Shelly attempt %d/%d failed: %s', attempt, SHELLY_RETRIES, e)
            if attempt < SHELLY_RETRIES and _stop_event.wait(SHELLY_RETRY_DELAY):
                break
    return None


# ---------------------------------------------------------------------------
# Database (writing)
# ---------------------------------------------------------------------------

def init_database(db_file):
    """Create the tables and indexes if needed. WAL mode is persistent in the file."""
    conn = sqlite3.connect(db_file, timeout=60)
    try:
        conn.execute('PRAGMA journal_mode=WAL;')
        for table in ('emeters0', 'emeters1'):
            conn.execute(
                f'CREATE TABLE IF NOT EXISTS {table} (timestamp DATETIME, power REAL, '
                'reactive REAL, voltage REAL, is_valid INT, total REAL, total_returned REAL);')
        conn.execute('CREATE TABLE IF NOT EXISTS relay (timestamp DATETIME, ison INT);')
        conn.execute(
            'CREATE TABLE IF NOT EXISTS temperatures (timestamp DATETIME, '
            'temp_1 REAL, temp_2 REAL, temp_3 REAL, temp_4 REAL, temp_5 REAL);')
        conn.execute('CREATE TABLE IF NOT EXISTS gpio (timestamp DATETIME, gpio_value INT);')
        for table in ('emeters0', 'emeters1', 'relay', 'temperatures', 'gpio'):
            conn.execute(f'CREATE INDEX IF NOT EXISTS idx_{table}_timestamp ON {table}(timestamp);')
        conn.commit()
    finally:
        conn.close()


def _write_shelly(c, timestamp, status):
    for device in (0, 1):
        em = status['emeters'][device]
        c.execute(
            f'INSERT INTO emeters{device} '
            '(timestamp, power, reactive, voltage, is_valid, total, total_returned) '
            'VALUES (?, ?, ?, ?, ?, ?, ?);',
            (timestamp, em['power'], em['reactive'], em['voltage'],
             1 if em['is_valid'] else 0, em['total'], em['total_returned']))

    relay_ison = status['relays'][0]['ison']
    c.execute('INSERT INTO relay (timestamp, ison) VALUES (?, ?);',
              (timestamp, 1 if relay_ison else 0))

    log.info('Power consumption: %s W | production: %s W | relay: %s',
             status['emeters'][0]['power'], status['emeters'][1]['power'], relay_ison)


def _write_temperatures_and_gpio(c, timestamp):
    _, temps = read_temperatures()
    log.info('Temperatures: %s', temps)
    c.execute(
        'INSERT INTO temperatures (timestamp, temp_1, temp_2, temp_3, temp_4, temp_5) '
        'VALUES (?, ?, ?, ?, ?, ?);', [timestamp] + temps)

    gpio_value = read_gpio(17)
    log.info('GPIO: %s', gpio_value)
    c.execute('INSERT INTO gpio (timestamp, gpio_value) VALUES (?, ?);',
              (timestamp, gpio_value))


def write_database(db_file, ip_shelly, polling_interval=60, temp_repetitions=2):
    """Main logging loop. Runs until SIGTERM / SIGINT.

    Every `polling_interval` seconds: log the Shelly EM and relay.
    Every `temp_repetitions` iterations: also log temperatures and GPIO
    (even if the Shelly is unreachable).
    A failure in one iteration is logged and never stops the loop.
    """
    polling_interval = int(polling_interval)
    temp_repetitions = int(temp_repetitions)

    # Clean stop on `systemctl stop` / kill / Ctrl-C
    def _handle_signal(signum, frame):
        log.info('Signal %s received, stopping.', signum)
        _stop_event.set()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    init_database(db_file)
    log.info('Logging started: db=%s shelly=%s interval=%ss temp every %d iterations',
             db_file, ip_shelly, polling_interval, temp_repetitions)

    counter_repetition = 0
    next_run = time.monotonic()

    while not _stop_event.is_set():
        try:
            timestamp = datetime.datetime.now().isoformat()
            status = get_shelly_status(ip_shelly)
            if status is None:
                log.error('Shelly unreachable, nothing logged for the power values.')

            counter_repetition += 1
            log_temps = counter_repetition >= temp_repetitions

            if status is not None or log_temps:
                conn = sqlite3.connect(db_file, timeout=60)
                try:
                    c = conn.cursor()
                    if status is not None:
                        _write_shelly(c, timestamp, status)
                    if log_temps:
                        _write_temperatures_and_gpio(c, timestamp)
                    conn.commit()
                finally:
                    conn.close()

            if log_temps:
                counter_repetition = 0

        except Exception:
            # Never let one bad iteration kill the logger
            log.exception('Iteration failed')

        # Fixed rhythm: compensate for the time spent working
        next_run += polling_interval
        delay = next_run - time.monotonic()
        if delay < 0:                       # we fell behind (e.g. long outage): resync
            next_run = time.monotonic()
            delay = 0
        _stop_event.wait(delay)

    log.info('Logging stopped.')


# ---------------------------------------------------------------------------
# Database (reading / display)
# ---------------------------------------------------------------------------

def read_database(db_file, days=2):
    """Return rows (timestamp, power_0, power_1, relay_state) of the last `days` days."""
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()

    conn = sqlite3.connect(db_file, timeout=60)
    try:
        c = conn.cursor()
        c.execute(
            """SELECT em0.timestamp, em0.power, em1.power, rel.ison
               FROM emeters0 AS em0
                    INNER JOIN emeters1 AS em1 ON em0.timestamp = em1.timestamp
                    INNER JOIN relay AS rel ON em0.timestamp = rel.timestamp
               WHERE em0.timestamp >= ?
               ORDER BY em0.timestamp;""", (cutoff,))
        return c.fetchall()
    finally:
        conn.close()


def plot_logdata(db_file, png_file):

    import matplotlib
    matplotlib.use('Agg')       # headless: no display needed
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    rows = read_database(db_file)
    if not rows:
        log.warning('No data to plot.')
        return

    # Reduction: keep every 4th point
    rows_red = rows[::4]

    times = [datetime.datetime.fromisoformat(r[0]) for r in rows_red]
    power_0 = [r[1] for r in rows_red]
    power_1 = [-r[2] for r in rows_red]
    relay_state = [r[3] for r in rows_red]

    fig, ax1 = plt.subplots(figsize=(10, 4))
    ax2 = ax1.twinx()

    ax1.plot(times, power_0, label='Consommation', color='b')
    ax1.plot(times, power_1, label='Production', color='r')
    ax2.plot(times, relay_state, label='Relais', color='g')

    ax1.set_xlabel('Date')
    ax1.set_ylabel('Puissance (W)')

    ax2.set_yticks([0, 1])
    ax2.set_ylim([0, 10])

    ax1.grid(True)

    fig.legend(loc='upper left')
    fig.tight_layout()

    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d %H:%M'))
    fig.autofmt_xdate()
    fig.savefig(png_file)
    plt.close(fig)


def display_logdata(db_file):

    from tabulate import tabulate

    rows = read_database(db_file)

    # 360 last lines (6 hours)
    rows1 = rows[-360:]

    print(tabulate(rows1[::-1], headers=["Date / Heure", "Conso.", "Prod.", "Relais"],
                   tablefmt="psql"))
    