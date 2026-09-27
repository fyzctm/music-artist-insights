import json
import os
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

ARTIST_NAME = "Armin van Buuren"

OUTPUT_DIR = Path("data/bronze/lastfm")
OUTPUT_FILE = OUTPUT_DIR / "armin_van_buuren_artist_info.json"


# --------------------------------------------------
# Extract
# --------------------------------------------------

params = {
    "method": "artist.getInfo",
    "artist": ARTIST_NAME,
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


# --------------------------------------------------
# Save Bronze data
# --------------------------------------------------

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

with OUTPUT_FILE.open("w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)


# --------------------------------------------------
# Quick validation
# --------------------------------------------------

artist = data["artist"]

print(f"Saved raw data to: {OUTPUT_FILE}")
print()
print("Artist:", artist.get("name"))
print("MusicBrainz ID:", artist.get("mbid"))
print("Listeners:", artist.get("stats", {}).get("listeners"))
print("Playcount:", artist.get("stats", {}).get("playcount"))