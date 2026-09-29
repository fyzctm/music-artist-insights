import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# Paths
# --------------------------------------------------

BRONZE_DIR = Path("data/bronze/lastfm")
SILVER_DIR = Path("data/silver/lastfm")


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def create_slug(value):
    """
    Convert an artist name into a filesystem-friendly slug.

    Example:
    Armin van Buuren -> armin_van_buuren
    Tiësto -> tiesto
    Above & Beyond -> above_beyond
    """

    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()

    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = value.strip("_")

    return value


# --------------------------------------------------
# Load Bronze data
# --------------------------------------------------

def load_bronze(artist_name):

    artist_slug = create_slug(artist_name)

    input_file = (
        BRONZE_DIR
        / f"{artist_slug}_artist_info.json"
    )

    if not input_file.exists():
        raise FileNotFoundError(
            f"Bronze Last.fm file not found: {input_file}"
        )

    with input_file.open(
        "r",
        encoding="utf-8",
    ) as f:
        data = json.load(f)

    return data, input_file


# --------------------------------------------------
# Build artist profile
# --------------------------------------------------

def build_profile(artist):

    stats = artist.get("stats", {})

    listeners = int(
        stats.get("listeners", 0)
    )

    playcount = int(
        stats.get("playcount", 0)
    )

    playcount_per_listener = (
        round(
            playcount / listeners,
            2,
        )
        if listeners > 0
        else None
    )

    snapshot_date = (
        datetime.now(timezone.utc)
        .date()
        .isoformat()
    )

    profile = {
        "artist_name": artist.get("name"),
        "mbid": artist.get("mbid"),
        "listeners": listeners,
        "playcount": playcount,
        "playcount_per_listener": playcount_per_listener,
        "snapshot_date": snapshot_date,
    }

    return profile


# --------------------------------------------------
# Save artist profile + snapshot history
# --------------------------------------------------

def save_profile(profile, artist_slug):

    SILVER_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    profile_file = (
        SILVER_DIR
        / f"{artist_slug}_artist_profile.csv"
    )

    snapshot_file = (
        SILVER_DIR
        / f"{artist_slug}_audience_snapshots.csv"
    )

    profile_df = pd.DataFrame(
        [profile]
    )

    profile_df.to_csv(
        profile_file,
        index=False,
    )

    snapshot_date = profile[
        "snapshot_date"
    ]

    if snapshot_file.exists():

        snapshots = pd.read_csv(
            snapshot_file
        )

        # Avoid duplicate snapshots when the
        # pipeline is run repeatedly on the same day.
        snapshots = snapshots[
            snapshots["snapshot_date"]
            != snapshot_date
        ]

        snapshots = pd.concat(
            [
                snapshots,
                profile_df,
            ],
            ignore_index=True,
        )

    else:

        snapshots = profile_df.copy()

    snapshots = snapshots.sort_values(
        "snapshot_date"
    )

    snapshots.to_csv(
        snapshot_file,
        index=False,
    )

    return (
        profile_df,
        snapshots,
        profile_file,
        snapshot_file,
    )


# --------------------------------------------------
# Build artist tags
# --------------------------------------------------

def build_tags(artist, artist_slug):

    tags = (
        artist
        .get("tags", {})
        .get("tag", [])
    )

    tag_rows = []

    for rank, tag in enumerate(
        tags,
        start=1,
    ):
        tag_rows.append(
            {
                "artist_mbid": artist.get("mbid"),
                "artist_name": artist.get("name"),
                "tag_rank": rank,
                "tag_name": tag.get("name"),
            }
        )

    tags_df = pd.DataFrame(
        tag_rows
    )

    tags_file = (
        SILVER_DIR
        / f"{artist_slug}_tags.csv"
    )

    tags_df.to_csv(
        tags_file,
        index=False,
    )

    return tags_df, tags_file


# --------------------------------------------------
# Build similar artists
# --------------------------------------------------

def build_similar_artists(
    artist,
    artist_slug,
):

    similar_artists = (
        artist
        .get("similar", {})
        .get("artist", [])
    )

    similar_rows = []

    for rank, similar_artist in enumerate(
        similar_artists,
        start=1,
    ):
        similar_rows.append(
            {
                "artist_mbid": artist.get("mbid"),
                "artist_name": artist.get("name"),
                "similar_artist_rank": rank,
                "similar_artist_name": (
                    similar_artist.get("name")
                ),
                "similar_artist_url": (
                    similar_artist.get("url")
                ),
            }
        )

    similar_df = pd.DataFrame(
        similar_rows
    )

    similar_file = (
        SILVER_DIR
        / f"{artist_slug}_similar_artists.csv"
    )

    similar_df.to_csv(
        similar_file,
        index=False,
    )

    return similar_df, similar_file


# --------------------------------------------------
# Run
# --------------------------------------------------

def main():

    if len(sys.argv) > 1:
        artist_name = " ".join(
            sys.argv[1:]
        )
    else:
        artist_name = "Armin van Buuren"

    artist_slug = create_slug(
        artist_name
    )

    data, input_file = load_bronze(
        artist_name
    )

    artist = data["artist"]

    # Use canonical artist name returned by Last.fm
    canonical_name = artist.get(
        "name",
        artist_name,
    )

    # Recreate slug from canonical name
    artist_slug = create_slug(
        canonical_name
    )

    profile = build_profile(
        artist
    )

    (
        profile_df,
        snapshots,
        profile_file,
        snapshot_file,
    ) = save_profile(
        profile,
        artist_slug,
    )

    (
        tags_df,
        tags_file,
    ) = build_tags(
        artist,
        artist_slug,
    )

    (
        similar_df,
        similar_file,
    ) = build_similar_artists(
        artist,
        artist_slug,
    )

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    print(
        "=== LAST.FM SILVER ARTIST PROFILE ==="
    )
    print()

    print(
        profile_df.to_string(
            index=False
        )
    )

    print()
    print(
        f"Bronze source: {input_file}"
    )
    print(
        f"Current profile saved to: {profile_file}"
    )
    print(
        f"Snapshot history saved to: {snapshot_file}"
    )

    print()
    print(
        f"Total historical snapshots: "
        f"{len(snapshots)}"
    )

    print()
    print(
        "=== LAST.FM ARTIST TAGS ==="
    )
    print(
        tags_df.to_string(
            index=False
        )
    )
    print(
        f"Tags saved to: {tags_file}"
    )

    print()
    print(
        "=== LAST.FM SIMILAR ARTISTS ==="
    )
    print(
        similar_df.to_string(
            index=False
        )
    )
    print(
        f"Similar artists saved to: "
        f"{similar_file}"
    )


if __name__ == "__main__":
    main()