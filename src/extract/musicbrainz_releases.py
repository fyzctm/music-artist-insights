import json
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests


BASE_URL = "https://musicbrainz.org/ws/2"

HEADERS = {
    "User-Agent": "MusicArtistInsights/0.1 (feyyazcitim@gmail.com)"
}

BRONZE_PATH = Path("data/bronze/musicbrainz")


def slugify_artist_name(name):
    """Convert an artist name into a safe filename slug."""

    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_name = ascii_name.lower()

    slug = re.sub(r"[^a-z0-9]+", "_", ascii_name)
    slug = slug.strip("_")

    return slug



def load_artist_search(artist_name):
    """
    Load the MusicBrainz artist-search result already stored
    in the Bronze layer.
    """

    slug = slugify_artist_name(artist_name)

    filepath = (
        BRONZE_PATH
        / f"{slug}_artist_search.json"
    )

    if not filepath.exists():
        raise FileNotFoundError(
            f"Artist search file not found: {filepath}\n"
            f"Run first:\n"
            f'python src/extract/musicbrainz_artist.py "{artist_name}"'
        )

    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)


def get_canonical_artist(artist_name):
    """
    Select the highest-ranked MusicBrainz artist search result.
    """

    data = load_artist_search(artist_name)

    artists = data.get("artists", [])

    if not artists:
        raise ValueError(
            f"No MusicBrainz artist results found for: {artist_name}"
        )

    artist = artists[0]

    return {
        "name": artist.get("name"),
        "mbid": artist.get("id"),
        "score": artist.get("score"),
    }


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
    "offset": offset,
    "inc": "artist-credits",
    "release-group-status": "website-default",
}

        max_retries = 3

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(
                    url,
                    headers=HEADERS,
                    params=params,
                    timeout=30,
                )

                response.raise_for_status()
                data = response.json()
                break

            except requests.exceptions.RequestException as exc:
                print(
                    f"Request failed at offset {offset} "
                    f"(attempt {attempt}/{max_retries}): {exc}"
                )

                if attempt == max_retries:
                    raise

                wait_seconds = attempt * 3
                print(f"Retrying in {wait_seconds} seconds...")
                time.sleep(wait_seconds)

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
            indent=2,
        )

    print(f"\nSaved raw data to: {filepath}")

    return filepath


def main():

    if len(sys.argv) < 2:
        artist_name = "Armin van Buuren"
    else:
        artist_name = " ".join(sys.argv[1:])

    artist = get_canonical_artist(artist_name)

    canonical_name = artist["name"]
    artist_mbid = artist["mbid"]

    print()
    print(f"Artist: {canonical_name}")
    print(f"MusicBrainz ID: {artist_mbid}")
    print(f"Search score: {artist['score']}")
    print()

    release_groups = get_release_groups(artist_mbid)

    slug = slugify_artist_name(canonical_name)

    output_file = save_raw_json(
        release_groups,
        f"{slug}_release_groups.json",
    )

    print()
    print(f"Total release groups: {len(release_groups)}")
    print(f"Output: {output_file}")


if __name__ == "__main__":
    main()