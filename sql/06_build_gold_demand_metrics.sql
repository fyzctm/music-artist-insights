-- ============================================================
-- Gold: Artist Demand Metrics
-- Purpose:
--   Summarise ListenBrainz demand evidence into an
--   analysis-ready artist-level Gold table.
-- ============================================================

CREATE OR REPLACE TABLE gold_artist_demand_metrics AS

WITH temporal AS (
    SELECT
    'Maddix' AS artist_name,
    artist_mbid,
    range,
    total_listens,
    unique_listeners,
    listens_per_listener,
    last_updated
    FROM read_csv_auto(
        'data/silver/listenbrainz/maddix_temporal_demand.csv'
    )
),

track_base AS (
    SELECT
        'Maddix' AS artist_name,
        *
    FROM read_csv_auto(
        'data/silver/listenbrainz/maddix_track_demand.csv'
    )
),

track_ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY artist_name
            ORDER BY total_listens DESC
        ) AS demand_rank,

        SUM(total_listens) OVER (
            PARTITION BY artist_name
        ) AS artist_track_listens
    FROM track_base
),

breadth AS (
    SELECT
        artist_name,
        MAX(artist_mbid) AS artist_mbid,
        COUNT(*) AS tracks_represented,
        SUM(total_listens) AS total_track_listens,

        ROUND(
            100.0 * SUM(CASE WHEN demand_rank = 1
                            THEN total_listens ELSE 0 END)
            / NULLIF(MAX(artist_track_listens), 0),
            2
        ) AS top1_share_pct,

        ROUND(
            100.0 * SUM(CASE WHEN demand_rank <= 5
                            THEN total_listens ELSE 0 END)
            / NULLIF(MAX(artist_track_listens), 0),
            2
        ) AS top5_share_pct,

        ROUND(
            100.0 * SUM(CASE WHEN demand_rank <= 10
                            THEN total_listens ELSE 0 END)
            / NULLIF(MAX(artist_track_listens), 0),
            2
        ) AS top10_share_pct

    FROM track_ranked
    GROUP BY artist_name
)

SELECT
    t.artist_name,
    t.artist_mbid,
    t.range,
    t.total_listens,
    t.unique_listeners,
    t.listens_per_listener,
    b.tracks_represented,
    b.total_track_listens,
    b.top1_share_pct,
    b.top5_share_pct,
    b.top10_share_pct,
    t.last_updated

FROM temporal t

LEFT JOIN breadth b
    ON t.artist_name = b.artist_name;