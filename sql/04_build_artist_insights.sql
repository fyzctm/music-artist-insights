CREATE OR REPLACE TABLE gold_artist_insights AS

WITH release_summary AS (

    SELECT
        artist_name,

        COUNT(*) AS total_releases,

        MIN(first_release_date) AS first_release_date,

        MAX(first_release_date) AS latest_release_date,

        COUNT(*) FILTER (
            WHERE primary_type = 'Album'
        ) AS albums,

        COUNT(*) FILTER (
            WHERE primary_type = 'Single'
        ) AS singles,

        COUNT(*) FILTER (
            WHERE primary_type = 'EP'
        ) AS eps

    FROM release_catalogue

    GROUP BY
        artist_name
),

latest_audience AS (

    SELECT
        artist_name,
        mbid,
        listeners,
        playcount,
        playcount_per_listener,
        snapshot_date

    FROM gold_lastfm_audience_metrics

    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY mbid
        ORDER BY snapshot_date DESC
    ) = 1
)

SELECT
    a.artist_name,
    a.mbid,

    r.first_release_date,
    r.latest_release_date,

    DATE_DIFF(
        'year',
        r.first_release_date,
        r.latest_release_date
    ) AS career_span_years,

    r.total_releases,
    r.albums,
    r.singles,
    r.eps,

    a.listeners,
    a.playcount,
    a.playcount_per_listener,
    a.snapshot_date AS audience_snapshot_date

FROM latest_audience a

LEFT JOIN release_summary r
    ON a.artist_name = r.artist_name

ORDER BY
    a.artist_name;