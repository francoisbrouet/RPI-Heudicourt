CREATE VIEW IF NOT EXISTS vwPlot AS
SELECT em0.[timestamp],
        em0.[power] as 'power_0',
        em1.[power] as 'power_1',
        rel.[ison] as 'relay_state'
FROM emeters0 AS em0
    INNER JOIN emeters1 AS em1 ON em0.[timestamp] = em1.[timestamp]
        INNER JOIN relay AS rel ON em0.[timestamp] = rel.[timestamp]

