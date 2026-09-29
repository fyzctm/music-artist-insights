import json
import os
import re
import sys
import unicodedata
from pathlib import Path

import requests
from dotenv import load_dotenv


# --------------------------------------------------
# Configuration
# --------------------------------------------------

load_dotenv()

API_KEY = os.getenv("LASTFM_API_KEY")

if not API_KEY:
    raise ValueError(
        "LASTFM_API_KEY was not found. "
        "Check that it exists in the project-root .env file."
    )

BASE_URL = "https://ws.audioscrobbler.com/2.0/"

OUTPUT_DIR = Path("data/bronze/lastfm")


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
# Extract
# --------------------------------------------------

def extract_lastfm_artist(artist_name):

    params = {
        "method": "artist.getInfo",
        "artist": artist_name,
        "api_key": API_KEY,
        "format": "json",
        "autocorrect": 1,
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if "error" in data:
        raise RuntimeError(
            f"Last.fm API error {data['error']}: "
            f"{data.get('message', 'Unknown error')}"
        )

    return data


# --------------------------------------------------
# Save Bronze data
# --------------------------------------------------

def save_bronze(data, artist_name):

    artist_slug = create_slug(artist_name)

    output_file = (
        OUTPUT_DIR
        / f"{artist_slug}_artist_info.json"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
        )

    return output_file


# --------------------------------------------------
# Run
# --------------------------------------------------

def main():

    if len(sys.argv) > 1:
        artist_name = " ".join(sys.argv[1:])
    else:
        artist_name = "Armin van Buuren"

    data = extract_lastfm_artist(
        artist_name
    )

    artist = data["artist"]

    # Use the canonical artist name returned by Last.fm
    canonical_name = artist.get(
        "name",
        artist_name,
    )

    output_file = save_bronze(
        data,
        canonical_name,
    )

    print(
        f"Saved raw data to: {output_file}"
    )
    print()
    print(
        "Artist:",
        canonical_name,
    )
    print(
        "MusicBrainz ID:",
        artist.get("mbid"),
    )
    print(
        "Listeners:",
        artist.get(
            "stats",
            {},
        ).get("listeners"),
    )
    print(
        "Playcount:",
        artist.get(
            "stats",
            {},
        ).get("playcount"),
    )


if __name__ == "__main__":
    main()