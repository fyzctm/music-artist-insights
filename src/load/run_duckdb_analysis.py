from pathlib import Path

import duckdb


DATABASE_FILE = Path(
    "music_artist_insights.duckdb"
)

SILVER_FILE = Path(
    "data/silver/musicbrainz/"
    "armin_van_buuren_release_catalogue.csv"
)

GOLD_SQL_FILE = Path(
    "sql/02_build_gold_release_metrics.sql"
)

GOLD_OUTPUT = Path(
    "data/gold/musicbrainz/"
    "release_metrics_by_year.csv"
)


def create_database():

    connection = duckdb.connect(
        str(DATABASE_FILE)
    )

    connection.execute(
        f"""
        CREATE OR REPLACE TABLE release_catalogue AS
        SELECT *
        FROM read_csv_auto('{SILVER_FILE}')
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


if __name__ == "__main__":

    con = create_database()

    print(
        "Silver rows loaded:",
        con.execute(
            "SELECT COUNT(*) FROM release_catalogue"
        ).fetchone()[0]
    )

    build_gold_metrics(con)

    print(
        "Gold rows created:",
        con.execute(
            "SELECT COUNT(*) FROM gold_release_metrics"
        ).fetchone()[0]
    )

    export_gold_metrics(con)

    print(
        f"Gold data saved to: {GOLD_OUTPUT}"
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

    print(results.to_string(index=False))

    con.close()