from pathlib import Path
import re
import unicodedata

import pandas as pd


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRONZE_PATH = (
    PROJECT_ROOT / "data" / "bronze" / "listenbrainz"
)

MUSICBRAINZ_SILVER_PATH = (
    PROJECT_ROOT / "data" / "silver" / "musicbrainz"
)

SILVER_PATH = (
    PROJECT_ROOT / "data" / "silver" / "listenbrainz"
)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def normalize_title(value):
    """
    Normalize track/release titles for catalogue matching.
    """

    if pd.isna(value):
        return None

    value = unicodedata.normalize("NFKD", str(value))
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower().strip()

    # Standardize punctuation/spacing.
    value = re.sub(r"[^\w\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    return value


def make_artist_slug(artist_name):
    """
    Convert artist name to the filename convention used by the project.
    """

    return (
        artist_name
        .lower()
        .replace("&", "and")
        .replace(" ", "_")
    )


# ---------------------------------------------------------
# Temporal demand
# ---------------------------------------------------------

def transform_temporal_demand(df):
    """
    Transform Bronze artist-level temporal demand.
    """

    df = df.copy()

    df["last_updated"] = pd.to_datetime(
        df["last_updated"],
        unit="s",
        errors="coerce"
    )

    df["listens_per_listener"] = (
        df["total_listens"] /
        df["unique_listeners"]
    )

    range_days = {
        "week": 7,
        "month": 30,
        "quarter": 90,
        "half_yearly": 180,
        "year": 365
    }

    df["range_days"] = df["range"].map(range_days)

    df["listens_per_day"] = (
        df["total_listens"] /
        df["range_days"]
    )

    df["listeners_per_day"] = (
        df["unique_listeners"] /
        df["range_days"]
    )

    return df


# ---------------------------------------------------------
# Track demand
# ---------------------------------------------------------

def transform_track_demand(df):
    """
    Transform cumulative track-level ListenBrainz demand.

    These values represent cumulative popularity/breadth,
    NOT temporal track demand.
    """

    df = df.copy()

    df["total_listens"] = pd.to_numeric(
        df["total_listens"],
        errors="coerce"
    )

    df["total_users"] = pd.to_numeric(
        df["total_users"],
        errors="coerce"
    )

    df = df.sort_values(
        "total_listens",
        ascending=False
    ).reset_index(drop=True)

    total_listens = df["total_listens"].sum()

    df["listen_share_pct"] = (
        df["total_listens"] /
        total_listens * 100
    )

    df["cumulative_share_pct"] = (
        df["listen_share_pct"].cumsum()
    )

    # Prefer release name where available because it aligns
    # more naturally with the MusicBrainz release catalogue.
    df["title_key"] = (
        df["release_name"]
        .fillna(df["recording_name"])
        .apply(normalize_title)
    )

    return df


# ---------------------------------------------------------
# Catalogue linkage
# ---------------------------------------------------------

def link_to_catalogue(track_df, catalogue_df, analysis_date):
    """
    Connect cumulative track demand to the MusicBrainz catalogue
    using normalized titles.

    The catalogue is expected to have unique title_key values
    after the earlier deduplication work.
    """

    tracks = track_df.copy()
    catalogue = catalogue_df.copy()

    catalogue["title_key"] = (
        catalogue["title"]
        .apply(normalize_title)
    )

    catalogue["first_release_date"] = pd.to_datetime(
        catalogue["first_release_date"],
        errors="coerce"
    )

    # Defensive check: don't silently allow a many-to-many merge.
    duplicate_titles = (
        catalogue["title_key"]
        .dropna()
        .duplicated()
        .sum()
    )

    if duplicate_titles > 0:
        raise ValueError(
            f"Catalogue contains {duplicate_titles} duplicate "
            "normalized title keys. Resolve before linking demand."
        )

    merged = tracks.merge(
        catalogue[
            [
                "title_key",
                "title",
                "first_release_date",
                "primary_type"
            ]
        ],
        on="title_key",
        how="left",
        indicator=True
    )

    analysis_date = pd.Timestamp(analysis_date)

    merged["release_age_days"] = (
        analysis_date -
        merged["first_release_date"]
    ).dt.days

    merged["catalogue_age"] = pd.cut(
        merged["release_age_days"],
        bins=[
            -1,
            365,
            365 * 3,
            float("inf")
        ],
        labels=[
            "Recent (≤1y)",
            "Mid catalogue (1–3y)",
            "Older catalogue (>3y)"
        ]
    )

    return merged


# ---------------------------------------------------------
# Quality checks
# ---------------------------------------------------------

def calculate_linkage_quality(df):
    """
    Calculate catalogue-linkage coverage.

    Listen coverage is particularly important because unmatched
    low-demand tracks may have limited analytical impact.
    """

    matched = df["_merge"] == "both"

    total_tracks = len(df)
    matched_tracks = matched.sum()

    total_listens = df["total_listens"].sum()

    matched_listens = df.loc[
        matched,
        "total_listens"
    ].sum()

    return pd.DataFrame({
        "metric": [
            "Demand tracks",
            "Matched tracks",
            "Track match rate (%)",
            "Total listens",
            "Matched listens",
            "Listen coverage (%)"
        ],
        "value": [
            total_tracks,
            matched_tracks,
            matched_tracks / total_tracks * 100
            if total_tracks else None,
            total_listens,
            matched_listens,
            matched_listens / total_listens * 100
            if total_listens else None
        ]
    })


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main(
    artist_name="Maddix",
    analysis_date="2026-10-03"
):
    artist_slug = make_artist_slug(artist_name)

    temporal_file = (
        BRONZE_PATH /
        f"{artist_slug}_temporal_demand.csv"
    )

    track_file = (
        BRONZE_PATH /
        f"{artist_slug}_track_demand.csv"
    )

    catalogue_file = (
        MUSICBRAINZ_SILVER_PATH /
        f"{artist_slug}_release_catalogue.csv"
    )

    print(f"Building Silver demand: {artist_name}")

    # -------------------------
    # Load
    # -------------------------

    temporal = pd.read_csv(temporal_file)
    tracks = pd.read_csv(track_file)
    catalogue = pd.read_csv(catalogue_file)

    # -------------------------
    # Transform
    # -------------------------

    temporal_silver = transform_temporal_demand(
        temporal
    )

    track_silver = transform_track_demand(
        tracks
    )

    track_catalogue_silver = link_to_catalogue(
        track_silver,
        catalogue,
        analysis_date
    )

    quality = calculate_linkage_quality(
        track_catalogue_silver
    )

    # -------------------------
    # Save
    # -------------------------

    SILVER_PATH.mkdir(
        parents=True,
        exist_ok=True
    )

    temporal_output = (
        SILVER_PATH /
        f"{artist_slug}_temporal_demand.csv"
    )

    track_output = (
        SILVER_PATH /
        f"{artist_slug}_track_demand.csv"
    )

    quality_output = (
        SILVER_PATH /
        f"{artist_slug}_demand_quality.csv"
    )

    temporal_silver.to_csv(
        temporal_output,
        index=False
    )

    track_catalogue_silver.to_csv(
        track_output,
        index=False
    )

    quality.to_csv(
        quality_output,
        index=False
    )

    print(f"Saved: {temporal_output}")
    print(f"Saved: {track_output}")
    print(f"Saved: {quality_output}")

    print("\nLinkage quality:")
    print(quality.round(2).to_string(index=False))


if __name__ == "__main__":
    main()