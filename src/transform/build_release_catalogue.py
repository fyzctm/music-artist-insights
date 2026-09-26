import json
from pathlib import Path

import pandas as pd


BRONZE_FILE = Path(
    "data/bronze/musicbrainz/"
    "armin_van_buuren_release_groups.json"
)

SILVER_PATH = Path("data/silver/musicbrainz")


def load_bronze_data():
    """Load raw MusicBrainz release-group data."""

    with open(BRONZE_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def transform_release_groups(release_groups):
    """Transform raw release groups into a clean analytical catalogue."""

    records = []

    for release in release_groups:

        secondary_types = release.get("secondary-types", [])

        records.append(
            {
                "release_group_id": release.get("id"),
                "title": release.get("title"),
                "primary_type": release.get("primary-type"),
                "first_release_date": release.get("first-release-date"),
                "is_compilation": "Compilation" in secondary_types,
                "is_remix": "Remix" in secondary_types,
                "is_live": "Live" in secondary_types,
                "is_dj_mix": "DJ-mix" in secondary_types,
            }
        )

    df = pd.DataFrame(records)

    # Keep the core analytical catalogue
    df = df[
        df["primary_type"].isin(
            ["Album", "Single", "EP"]
        )
    ].copy()

    # Remove releases without a usable date
    df = df[
        df["first_release_date"].notna()
        & (df["first_release_date"] != "")
    ].copy()

    df["first_release_date"] = pd.to_datetime(
        df["first_release_date"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["first_release_date"]
    )

    df = df.sort_values(
        "first_release_date"
    )

    return df


def save_silver_data(df):

    SILVER_PATH.mkdir(
        parents=True,
        exist_ok=True
    )

    filepath = (
        SILVER_PATH
        / "armin_van_buuren_release_catalogue.csv"
    )

    df.to_csv(
        filepath,
        index=False
    )

    print(f"Saved Silver data to: {filepath}")


if __name__ == "__main__":

    release_groups = load_bronze_data()

    catalogue = transform_release_groups(
        release_groups
    )

    save_silver_data(catalogue)

    print(f"\nSilver catalogue rows: {len(catalogue)}")

    print("\nRelease types:")
    print(
        catalogue["primary_type"]
        .value_counts()
    )

    print("\nDate range:")
    print(
        catalogue["first_release_date"].min(),
        "to",
        catalogue["first_release_date"].max()
    )

    print("\nFirst 10 releases:")
    print(
        catalogue[
            [
                "first_release_date",
                "primary_type",
                "title"
            ]
        ].head(10)
    )
    