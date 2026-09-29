CREATE OR REPLACE TABLE gold_release_metrics AS

WITH parameters AS (

    SELECT
        artist_name,

        MAX(first_release_date) AS data_through_date,

        YEAR(MAX(first_release_date)) AS current_year,

        MONTH(MAX(first_release_date)) AS cutoff_month,

        DAY(MAX(first_release_date)) AS cutoff_day

    FROM release_catalogue

    GROUP BY
        artist_name
),

yearly_metrics AS (

    SELECT
        r.artist_name,

        YEAR(r.first_release_date) AS release_year,

        COUNT(*) AS total_releases,

        COUNT(*) FILTER (
            WHERE r.is_remix = FALSE
              AND r.is_compilation = FALSE
              AND r.is_live = FALSE
              AND r.is_dj_mix = FALSE
        ) AS core_releases,

        COUNT(*) FILTER (
            WHERE r.primary_type = 'Single'
        ) AS singles,

        COUNT(*) FILTER (
            WHERE r.primary_type = 'Album'
        ) AS albums,

        COUNT(*) FILTER (
            WHERE r.primary_type = 'EP'
        ) AS eps,

        COUNT(*) FILTER (
            WHERE r.is_remix = TRUE
        ) AS remixes,

        COUNT(*) FILTER (
            WHERE r.is_compilation = TRUE
        ) AS compilations,

        COUNT(*) FILTER (
            WHERE r.is_dj_mix = TRUE
        ) AS dj_mixes,

        COUNT(*) FILTER (
            WHERE r.is_live = TRUE
        ) AS live_releases

    FROM release_catalogue r

    GROUP BY
        r.artist_name,
        YEAR(r.first_release_date)
),

with_previous_year AS (

    SELECT
        *,

        LAG(total_releases) OVER (
            PARTITION BY artist_name
            ORDER BY release_year
        ) AS previous_year_releases

    FROM yearly_metrics
),

ytd_metrics AS (

    SELECT
        r.artist_name,

        YEAR(r.first_release_date) AS release_year,

        COUNT(*) FILTER (
            WHERE
                MONTH(r.first_release_date) < p.cutoff_month

                OR (
                    MONTH(r.first_release_date) = p.cutoff_month
                    AND DAY(r.first_release_date) <= p.cutoff_day
                )
        ) AS comparable_ytd_releases,

        COUNT(*) FILTER (
            WHERE
                (
                    MONTH(r.first_release_date) < p.cutoff_month

                    OR (
                        MONTH(r.first_release_date) = p.cutoff_month
                        AND DAY(r.first_release_date) <= p.cutoff_day
                    )
                )

                AND r.is_remix = FALSE
                AND r.is_compilation = FALSE
                AND r.is_live = FALSE
                AND r.is_dj_mix = FALSE
        ) AS comparable_ytd_core_releases

    FROM release_catalogue r

    INNER JOIN parameters p
        ON r.artist_name = p.artist_name

    GROUP BY
        r.artist_name,
        YEAR(r.first_release_date)
)

SELECT
    y.artist_name,
    y.release_year,

    y.total_releases,
    y.core_releases,
    y.singles,
    y.albums,
    y.eps,
    y.remixes,
    y.compilations,
    y.dj_mixes,
    y.live_releases,

    y.previous_year_releases,

    y.total_releases
        - y.previous_year_releases
        AS yoy_release_change,

    ROUND(
        100.0
        * (
            y.total_releases
            - y.previous_year_releases
        )
        / NULLIF(y.previous_year_releases, 0),
        1
    ) AS yoy_release_pct,

    d.comparable_ytd_releases,
    d.comparable_ytd_core_releases,

    p.data_through_date
        AS dataset_through_date

FROM with_previous_year y

LEFT JOIN ytd_metrics d
    ON y.artist_name = d.artist_name
    AND y.release_year = d.release_year

INNER JOIN parameters p
    ON y.artist_name = p.artist_name

ORDER BY
    y.artist_name,
    y.release_year;