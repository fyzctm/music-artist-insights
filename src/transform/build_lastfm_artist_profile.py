import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# Paths
# --------------------------------------------------

INPUT_FILE = Path(
    "data/bronze/lastfm/armin_van_buuren_artist_info.json"
)

OUTPUT_DIR = Path("data/silver/lastfm")

PROFILE_FILE = OUTPUT_DIR / "armin_van_buuren_artist_profile.csv"

SNAPSHOT_FILE = OUTPUT_DIR / "armin_van_buuren_audience_snapshots.csv"


# --------------------------------------------------
# Load Bronze data
# --------------------------------------------------

with INPUT_FILE.open("r", encoding="utf-8") as f:
    data = json.load(f)

artist = data["artist"]

stats = artist.get("stats", {})


# --------------------------------------------------
# Transform
# --------------------------------------------------

listeners = int(stats.get("listeners", 0))
playcount = int(stats.get("playcount", 0))

playcount_per_listener = (
    round(playcount / listeners, 2)
    if listeners > 0
    else None
)

snapshot_date = datetime.now(timezone.utc).date().isoformat()

profile = {
    "artist_name": artist.get("name"),
    "mbid": artist.get("mbid"),
    "listeners": listeners,
    "playcount": playcount,
    "playcount_per_listener": playcount_per_listener,
    "snapshot_date": snapshot_date,
}


# --------------------------------------------------
# Save current Silver profile
# --------------------------------------------------

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

profile_df = pd.DataFrame([profile])

profile_df.to_csv(
    PROFILE_FILE,
    index=False,
)


# --------------------------------------------------
# Maintain historical snapshots
# --------------------------------------------------

if SNAPSHOT_FILE.exists():

    snapshots = pd.read_csv(SNAPSHOT_FILE)

    # Avoid creating duplicate snapshots
    # if pipeline is run repeatedly on the same day.
    snapshots = snapshots[
        snapshots["snapshot_date"] != snapshot_date
    ]

    snapshots = pd.concat(
        [snapshots, profile_df],
        ignore_index=True,
    )

else:

    snapshots = profile_df.copy()


snapshots = snapshots.sort_values("snapshot_date")

snapshots.to_csv(
    SNAPSHOT_FILE,
    index=False,
)


# --------------------------------------------------
# Validation
# --------------------------------------------------

print("=== LAST.FM SILVER ARTIST PROFILE ===")
print()

print(profile_df.to_string(index=False))

print()
print(f"Current profile saved to: {PROFILE_FILE}")
print(f"Snapshot history saved to: {SNAPSHOT_FILE}")

print()
print(f"Total historical snapshots: {len(snapshots)}")

# ---------------------------------------------------------
# Build artist tags
# ---------------------------------------------------------

tags = artist.get("tags", {}).get("tag", [])

tag_rows = []

for rank, tag in enumerate(tags, start=1):
    tag_rows.append(
    {
        "artist_mbid": artist.get("mbid"),
        "artist_name": artist.get("name"),
        "tag_rank": rank,
        "tag_name": tag.get("name"),
    }
)

tags_df = pd.DataFrame(tag_rows)

TAGS_FILE = OUTPUT_DIR / "armin_van_buuren_tags.csv"
tags_df.to_csv(TAGS_FILE, index=False)

print()
print("=== LAST.FM ARTIST TAGS ===")
print(tags_df.to_string(index=False))
print(f"Tags saved to: {TAGS_FILE}")


# ---------------------------------------------------------
# Build similar artists
# ---------------------------------------------------------

similar_artists = artist.get("similar", {}).get("artist", [])

similar_rows = []

for rank, similar_artist in enumerate(similar_artists, start=1):
    similar_rows.append(
    {
        "artist_mbid": artist.get("mbid"),
        "artist_name": artist.get("name"),
        "similar_artist_rank": rank,
        "similar_artist_name": similar_artist.get("name"),
        "similar_artist_url": similar_artist.get("url"),
    }
)

similar_df = pd.DataFrame(similar_rows)

SIMILAR_FILE = OUTPUT_DIR / "armin_van_buuren_similar_artists.csv"
similar_df.to_csv(SIMILAR_FILE, index=False)

print()
print("=== LAST.FM SIMILAR ARTISTS ===")
print(similar_df.to_string(index=False))
print(f"Similar artists saved to: {SIMILAR_FILE}")