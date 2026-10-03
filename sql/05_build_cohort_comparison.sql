CREATE OR REPLACE TABLE gold_cohort_comparison AS

WITH cohort AS (

    SELECT *
    FROM read_csv_auto(
        'config/artists.csv',
        header = true
    )

),

spotify AS (

    SELECT
        artist_name,
        CAST(snapshot_date AS DATE) AS spotify_snapshot_date,
        spotify_monthly_listeners,
        spotify_followers
    FROM read_csv_auto(
        'data/manual/spotify_artist_snapshot.csv',
        header = true
    )

),

latest_lastfm AS (

    SELECT
        artist_name,
        mbid,
        snapshot_date AS lastfm_snapshot_date,
        listeners AS lastfm_listeners,
        playcount AS lastfm_playcount,
        playcount_per_listener AS audience_intensity

    FROM gold_lastfm_audience_metrics

    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY artist_name
        ORDER BY snapshot_date DESC
    ) = 1

),

catalogue AS (

    SELECT
        artist_name,
        first_release_date,
        latest_release_date,
        career_span_years,
        total_releases,
        albums,
        singles,
        eps

    FROM gold_artist_insights

)

SELECT

    c.artist_name,
    c.context_role,
    c.context_scope,
    g.first_release_date,
    g.latest_release_date,
    g.career_span_years,
    g.total_releases,
    g.albums,
    g.singles,
    g.eps,
    s.spotify_snapshot_date,
    s.spotify_monthly_listeners,
    s.spotify_followers,

    l.mbid,
    l.lastfm_snapshot_date,
    l.lastfm_listeners,
    l.lastfm_playcount,
    l.audience_intensity

FROM cohort c

LEFT JOIN spotify s
    ON c.artist_name = s.artist_name

LEFT JOIN latest_lastfm l
    ON c.artist_name = l.artist_name

LEFT JOIN catalogue g
    ON c.artist_name = g.artist_name

ORDER BY c.artist_name;