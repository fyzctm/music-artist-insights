import json
import time
from pathlib import Path

import requests


BASE_URL = "https://musicbrainz.org/ws/2"

HEADERS = {
    "User-Agent": "MusicArtistInsights/0.1 (feyyazcitim@gmail.com)"
}

BRONZE_PATH = Path("data/bronze/musicbrainz")

ARTIST_MBID = "477b8c0c-c5fc-4ad2-b5b2-191f0bf2a9df"


def get_release_groups(artist_mbid):
    """Retrieve all release groups for a MusicBrainz artist."""

    url = f"{BASE_URL}/release-group"

    limit = 100
    offset = 0
    all_release_groups = []

    while True:

        params = {
            "artist": artist_mbid,
            "fmt": "json",
            "limit": limit,
            "offset": offset
        }

        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        release_groups = data.get("release-groups", [])

        all_release_groups.extend(release_groups)

        print(
            f"Retrieved {len(release_groups)} records "
            f"(offset {offset})"
        )

        if len(release_groups) < limit:
            break

        offset += limit

        # Respect MusicBrainz rate limits
        time.sleep(1.1)

    return all_release_groups


def save_raw_json(data, filename):
    """Save API response to the Bronze layer."""

    BRONZE_PATH.mkdir(parents=True, exist_ok=True)

    filepath = BRONZE_PATH / filename

    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(f"\nSaved raw data to: {filepath}")


if __name__ == "__main__":

    release_groups = get_release_groups(ARTIST_MBID)

    save_raw_json(
        release_groups,
        "armin_van_buuren_release_groups.json"
    )

    print(f"Total release groups: {len(release_groups)}")