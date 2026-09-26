import json
from pathlib import Path

import requests


BASE_URL = "https://musicbrainz.org/ws/2"

HEADERS = {
    "User-Agent": "MusicArtistInsights/0.1 (feyyazcitim@gmail.com)"
}

BRONZE_PATH = Path("data/bronze/musicbrainz")


def search_artist(artist_name):
    """Search MusicBrainz for an artist."""

    url = f"{BASE_URL}/artist"

    params = {
        "query": f'artist:"{artist_name}"',
        "fmt": "json",
        "limit": 5
    }

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def save_raw_json(data, filename):
    """Save raw API response to the Bronze layer."""

    BRONZE_PATH.mkdir(parents=True, exist_ok=True)

    filepath = BRONZE_PATH / filename

    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(f"Saved raw data to: {filepath}")


if __name__ == "__main__":

    artist_name = "Armin van Buuren"

    data = search_artist(artist_name)

    save_raw_json(
        data,
        "armin_van_buuren_artist_search.json"
    )

    for artist in data["artists"]:
        print(
            artist["name"],
            "|",
            artist.get("country"),
            "|",
            artist["id"],
            "| score:",
            artist.get("score")
        )