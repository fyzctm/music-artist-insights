import json
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd


BRONZE_PATH = Path("data/bronze/musicbrainz")
SILVER_PATH = Path("data/silver/musicbrainz")


def make_artist_slug(artist_name):
    """
    Convert an artist name into a consistent, file-safe slug.

    Examples:
    Armin van Buuren -> armin_van_buuren
    Tiësto -> tiesto
    Above & Beyond -> above_beyond
    """

    normalized = unicodedata.normalize("NFKD", artist_name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_name = ascii_name.lower()

    slug = re.sub(r"[^a-z0-9]+", "_", ascii_name)
    slug = slug.strip("_")

    return slug


def load_bronze_data(artist_slug):
    """Load raw MusicBrainz release-group data."""

    bronze_file = (
        BRONZE_PATH
        / f"{artist_slug}_release_groups.json"
    )

    with open(bronze_file, "r", encoding="utf-8") as file:
        return json.load(file)


def transform_release_groups(
    release_groups,
    artist_name
):
    """Transform raw release groups into a clean analytical catalogue."""

    records = []

    for release in release_groups:

        secondary_types = release.get("secondary-types", [])

        records.append(
            {
                "artist_name": artist_name,
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
    format="mixed",
    errors="coerce"
)

    df = df.dropna(
        subset=["first_release_date"]
    )

    # Deduplicate MusicBrainz release groups that represent
# the same analytical release.
    df = df.drop_duplicates(
    subset=[
        "artist_name",
        "title",
        "first_release_date",
        "primary_type",
    ],
    keep="first",
)
    df = df.sort_values(
        "first_release_date"
    )

    return df

def save_silver_data(df, artist_slug):
    """Save the transformed catalogue to the Silver layer."""

    SILVER_PATH.mkdir(
        parents=True,
        exist_ok=True
    )

    filepath = (
        SILVER_PATH
        / f"{artist_slug}_release_catalogue.csv"
    )

    df.to_csv(
        filepath,
        index=False
    )

    print(f"Saved Silver data to: {filepath}")


def main():

    artist_name = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Armin van Buuren"
    )

    artist_slug = make_artist_slug(artist_name)

    print(f"Artist: {artist_name}")
    print(f"Artist slug: {artist_slug}")

    release_groups = load_bronze_data(
        artist_slug
    )

    catalogue = transform_release_groups(
    release_groups,
    artist_name
)

    save_silver_data(
        catalogue,
        artist_slug
    )

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


if __name__ == "__main__":
    main()