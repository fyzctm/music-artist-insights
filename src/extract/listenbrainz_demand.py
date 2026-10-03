import os
import time
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    retry = Retry(
        total=4,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )

    session = requests.Session()

    adapter = HTTPAdapter(max_retries=retry)

    session.mount("https://", adapter)

    return session


SESSION = create_session()

load_dotenv()

BASE_URL = "https://api.listenbrainz.org/1"
TOKEN = os.getenv("LISTENBRAINZ_TOKEN")

HEADERS = {
    "Authorization": f"Token {TOKEN}"
} if TOKEN else {}

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRONZE_PATH = PROJECT_ROOT / "data" / "bronze" / "listenbrainz"


def fetch_artist_temporal_demand(artist_mbid):
    """
    Fetch artist-level ListenBrainz demand across supported time windows.
    """

    ranges = ["week", "month", "quarter", "half_yearly", "year"]
    rows = []

    for range_name in ranges:
        url = f"{BASE_URL}/stats/artist/{artist_mbid}/listeners"

        response = SESSION.get(
            url,
            params={"range": range_name},
            headers=HEADERS,
            timeout=60
        )
        response.raise_for_status()

        payload = response.json()["payload"]

        rows.append({
            "artist_mbid": artist_mbid,
            "range": range_name,
            "total_listens": payload.get("total_listen_count"),
            "unique_listeners": payload.get("total_user_count"),
            "last_updated": payload.get("last_updated")
        })

        time.sleep(0.2)

    return pd.DataFrame(rows)


def fetch_artist_track_demand(artist_mbid, count=1000):
    """
    Fetch cumulative track-level popularity for an artist.

    IMPORTANT:
    This endpoint does NOT provide reliable temporal track demand.
    Values should be interpreted as cumulative popularity/breadth only.
    """

    url = (
        f"{BASE_URL}/popularity/"
        f"top-recordings-for-artist/{artist_mbid}"
    )

    response = SESSION.get(
        url,
        params={"count": count},
        headers=HEADERS,
        timeout=60
    )
    response.raise_for_status()

    payload = response.json()

    # Endpoint currently returns payload directly as a list.
    recordings = (
        payload["payload"]
        if isinstance(payload, dict) and "payload" in payload
        else payload
    )

    rows = []

    for item in recordings:
        rows.append({
            "artist_mbid": artist_mbid,
            "recording_name": item.get("recording_name"),
            "release_name": item.get("release_name"),
            "recording_mbid": item.get("recording_mbid"),
            "release_mbid": item.get("release_mbid"),
            "total_listens": item.get("total_listen_count"),
            "total_users": item.get("total_user_count")
        })

    return pd.DataFrame(rows)


def save_bronze(df, filename):
    """
    Save extracted ListenBrainz data without analytical transformation.
    """

    BRONZE_PATH.mkdir(
        parents=True,
        exist_ok=True
    )

    filepath = BRONZE_PATH / filename

    df.to_csv(
        filepath,
        index=False
    )

    print(f"Saved: {filepath}")

    return filepath

if __name__ == "__main__":

    MADDIX_MBID = "0ae6eb0e-f5b4-48b0-98ab-2158ccd6f5c8"

    print("Fetching Maddix temporal demand...")
    temporal = fetch_artist_temporal_demand(MADDIX_MBID)

    print(temporal)

    save_bronze(
        temporal,
        "maddix_temporal_demand.csv"
    )

    print("\nFetching Maddix track demand...")
    tracks = fetch_artist_track_demand(MADDIX_MBID)

    print(f"Tracks returned: {len(tracks)}")
    print(tracks.head())

    save_bronze(
        tracks,
        "maddix_track_demand.csv"
    )