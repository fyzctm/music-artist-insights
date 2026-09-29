import json
import re
import sys
import unicodedata
from pathlib import Path

import requests


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_URL = "https://musicbrainz.org/ws/2"

HEADERS = {
    "User-Agent": "MusicArtistInsights/0.1 (feyyazcitim@gmail.com)"
}

BRONZE_PATH = Path("data/bronze/musicbrainz")


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

def search_artist(artist_name):
    """Search MusicBrainz for an artist."""

    url = f"{BASE_URL}/artist"

    params = {
        "query": f'artist:"{artist_name}"',
        "fmt": "json",
        "limit": 5,
    }

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


# --------------------------------------------------
# Save Bronze data
# --------------------------------------------------

def save_raw_json(data, artist_name):

    artist_slug = create_slug(
        artist_name
    )

    filename = (
        f"{artist_slug}_artist_search.json"
    )

    BRONZE_PATH.mkdir(
        parents=True,
        exist_ok=True,
    )

    filepath = (
        BRONZE_PATH / filename
    )

    with filepath.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return filepath


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

    data = search_artist(
        artist_name
    )

    filepath = save_raw_json(
        data,
        artist_name,
    )

    print(
        f"Saved raw data to: {filepath}"
    )

    print()
    print(
        f"MusicBrainz search results for: "
        f"{artist_name}"
    )
    print()

    for rank, artist in enumerate(
        data.get("artists", []),
        start=1,
    ):

        print(
            f"{rank}. "
            f"{artist.get('name')} "
            f"| country: {artist.get('country')} "
            f"| MBID: {artist.get('id')} "
            f"| score: {artist.get('score')}"
        )


if __name__ == "__main__":
    main()