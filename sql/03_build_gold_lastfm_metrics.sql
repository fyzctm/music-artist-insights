CREATE OR REPLACE TABLE gold_lastfm_audience_metrics AS

WITH audience AS (
    SELECT
        artist_name,
        mbid,
        listeners,
        playcount,
        playcount_per_listener,
        CAST(snapshot_date AS DATE) AS snapshot_date,

        LAG(listeners) OVER (
            PARTITION BY mbid
            ORDER BY CAST(snapshot_date AS DATE)
        ) AS previous_listeners,

        LAG(playcount) OVER (
            PARTITION BY mbid
            ORDER BY CAST(snapshot_date AS DATE)
        ) AS previous_playcount

    FROM lastfm_audience_snapshots
)

SELECT
    artist_name,
    mbid,
    snapshot_date,

    listeners,
    playcount,
    playcount_per_listener,

    previous_listeners,
    listeners - previous_listeners AS listener_change,

    CASE
        WHEN previous_listeners > 0
        THEN ROUND(
            100.0 * (listeners - previous_listeners)
            / previous_listeners,
            2
        )
    END AS listener_growth_pct,

    previous_playcount,
    playcount - previous_playcount AS playcount_change,

    CASE
        WHEN previous_playcount > 0
        THEN ROUND(
            100.0 * (playcount - previous_playcount)
            / previous_playcount,
            2
        )
    END AS playcount_growth_pct

FROM audience
ORDER BY snapshot_date;