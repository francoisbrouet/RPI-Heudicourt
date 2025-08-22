#/usr/bin/python3

import sqlite3
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


conn = sqlite3.connect ('../database/logdata.db')
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
            FROM vwPlot            
            ORDER BY [timestamp]"""
c.execute(sql)
rows = c.fetchall()
conn.close()

print (len(rows), 'records')

time = [datetime.datetime.fromisoformat(r[0]) for r in rows]
power_0 = [r[1] for r in rows]
power_1 = [-r[2] for r in rows]
relay_state = [r[3] for r in rows]

fig, ax1 = plt.subplots(figsize=(10, 4))
#fig = plt.figure(figsize=(10, 4))


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

fig.legend(loc='upper right')
fig.tight_layout()

fig.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b-%d %H:%M'))
plt.gcf().autofmt_xdate()
fig.savefig('./solaire_graph.png')





