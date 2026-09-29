from pathlib import Path

import duckdb


DATABASE_FILE = Path(
    "music_artist_insights.duckdb"
)

MUSICBRAINZ_SILVER_PATH = Path(
    "data/silver/musicbrainz"
)

GOLD_SQL_FILE = Path(
    "sql/02_build_gold_release_metrics.sql"
)

GOLD_OUTPUT = Path(
    "data/gold/musicbrainz/"
    "release_metrics_by_year.csv"
)

LASTFM_SILVER_PATH = Path(
    "data/silver/lastfm"
)

LASTFM_GOLD_SQL_FILE = Path(
    "sql/03_build_gold_lastfm_metrics.sql"
)

ARTIST_INSIGHTS_SQL_FILE = Path(
    "sql/04_build_artist_insights.sql"
)


def create_database():

    connection = duckdb.connect(
        str(DATABASE_FILE)
    )

    silver_pattern = (
        MUSICBRAINZ_SILVER_PATH
        / "*_release_catalogue.csv"
    )

    connection.execute(
        f"""
        CREATE OR REPLACE TABLE release_catalogue AS
        SELECT *
        FROM read_csv_auto(
            '{silver_pattern}',
            union_by_name = TRUE
        )
        """
    )

    return connection


def build_gold_metrics(connection):

    sql = GOLD_SQL_FILE.read_text(
        encoding="utf-8"
    )

    connection.execute(sql)


def export_gold_metrics(connection):

    GOLD_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection.execute(
        f"""
        COPY gold_release_metrics
        TO '{GOLD_OUTPUT}'
        (HEADER, DELIMITER ',')
        """
    )


def load_lastfm_silver(connection):

    profile_pattern = (
        LASTFM_SILVER_PATH
        / "*_artist_profile.csv"
    )

    snapshots_pattern = (
        LASTFM_SILVER_PATH
        / "*_audience_snapshots.csv"
    )

    tags_pattern = (
        LASTFM_SILVER_PATH
        / "*_tags.csv"
    )

    similar_pattern = (
        LASTFM_SILVER_PATH
        / "*_similar_artists.csv"
    )

    connection.execute(
        f"""
        CREATE OR REPLACE TABLE lastfm_artist_profile AS
        SELECT *
        FROM read_csv_auto('{profile_pattern}')
        """
    )

    connection.execute(
        f"""
        CREATE OR REPLACE TABLE lastfm_audience_snapshots AS
        SELECT *
        FROM read_csv_auto('{snapshots_pattern}')
        """
    )

    connection.execute(
        f"""
        CREATE OR REPLACE TABLE lastfm_artist_tags AS
        SELECT *
        FROM read_csv_auto('{tags_pattern}')
        """
    )

    connection.execute(
        f"""
        CREATE OR REPLACE TABLE lastfm_similar_artists AS
        SELECT *
        FROM read_csv_auto('{similar_pattern}')
        """
    )


def build_lastfm_gold(connection):

    sql = LASTFM_GOLD_SQL_FILE.read_text(
        encoding="utf-8"
    )

    connection.execute(sql)


def build_artist_insights(connection):

    sql = ARTIST_INSIGHTS_SQL_FILE.read_text(
        encoding="utf-8"
    )

    connection.execute(sql)


if __name__ == "__main__":

    con = create_database()

    print(
        "Silver rows loaded:",
        con.execute(
            "SELECT COUNT(*) FROM release_catalogue"
        ).fetchone()[0]
    )

    print("\nArtists loaded:")

    artists = con.execute(
        """
        SELECT
            artist_name,
            COUNT(*) AS release_rows,
            MIN(first_release_date) AS first_release,
            MAX(first_release_date) AS latest_release
        FROM release_catalogue
        GROUP BY artist_name
        ORDER BY artist_name
        """
    ).fetchdf()

    print(
        artists.to_string(index=False)
    )

    build_gold_metrics(con)

    print(
        "\nGold rows created:",
        con.execute(
            "SELECT COUNT(*) FROM gold_release_metrics"
        ).fetchone()[0]
    )

    export_gold_metrics(con)

    print(
        f"Gold data saved to: {GOLD_OUTPUT}"
    )

    load_lastfm_silver(con)

    print(
        "Last.fm Silver tables loaded."
    )

    build_lastfm_gold(con)

    print(
        "Last.fm Gold metrics created."
    )

    print("\nLatest Gold metrics:")

    results = con.execute(
        """
        SELECT *
        FROM gold_release_metrics
        ORDER BY release_year DESC
        LIMIT 10
        """
    ).fetchdf()

    print(
        results.to_string(index=False)
    )

    print("\nLatest Last.fm Gold metrics:")

    lastfm_results = con.execute(
        """
        SELECT *
        FROM gold_lastfm_audience_metrics
        ORDER BY snapshot_date DESC
        LIMIT 10
        """
    ).fetchdf()

    print(
        lastfm_results.to_string(index=False)
    )

    build_artist_insights(con)

    print(
        "\nUnified Artist Gold insights created."
    )

    artist_results = con.execute(
        """
        SELECT *
        FROM gold_artist_insights
        """
    ).fetchdf()

    print("\nUnified Artist Insights:")

    print(
        artist_results.to_string(index=False)
    )

    con.close()