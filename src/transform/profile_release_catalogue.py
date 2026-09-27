from pathlib import Path

import pandas as pd


SILVER_FILE = Path(
    "data/silver/musicbrainz/"
    "armin_van_buuren_release_catalogue.csv"
)


def load_catalogue():
    """Load the Silver release catalogue."""

    return pd.read_csv(
        SILVER_FILE,
        parse_dates=["first_release_date"]
    )


def profile_catalogue(df):
    """Run basic quality and catalogue profiling checks."""

    print("\n=== SILVER CATALOGUE PROFILE ===")

    print(f"\nTotal releases: {len(df)}")

    print("\nRelease types:")
    print(
        df["primary_type"]
        .value_counts()
    )

    print("\nSecondary classifications:")
    for column in [
        "is_remix",
        "is_compilation",
        "is_live",
        "is_dj_mix"
    ]:
        print(
            f"{column}: "
            f"{df[column].sum()}"
        )

    print("\nDuplicate titles:")
    duplicates = (
        df[df.duplicated("title", keep=False)]
        .sort_values("title")
    )

    print(
        f"{duplicates['title'].nunique()} "
        "titles occur more than once"
    )

    print("\nTop duplicate titles:")
    print(
        df["title"]
        .value_counts()
        .head(15)
    )

    print("\nReleases by year:")
    releases_by_year = (
        df.assign(
            year=df["first_release_date"].dt.year
        )
        .groupby("year")
        .size()
    )

    print(releases_by_year.to_string())

    print("\nHighest-volume years:")
    print(
        releases_by_year
        .sort_values(ascending=False)
        .head(10)
    )


if __name__ == "__main__":

    catalogue = load_catalogue()

    profile_catalogue(catalogue)
    