import subprocess
import sys


ARTISTS = [
    "Above & Beyond",
    "Hardwell",
    "Maddix",
    "ARTBAT",
    "Ben Gold",
]


PIPELINE_STEPS = [
    (
        "MusicBrainz artist resolution",
        "src/extract/musicbrainz_artist.py",
    ),
    (
        "MusicBrainz release extraction",
        "src/extract/musicbrainz_releases.py",
    ),
    (
        "MusicBrainz Silver catalogue",
        "src/transform/build_release_catalogue.py",
    ),
    (
        "Last.fm extraction",
        "src/extract/lastfm_artist.py",
    ),
    (
        "Last.fm Silver profile",
        "src/transform/build_lastfm_artist_profile.py",
    ),
]


def run_step(artist_name, step_name, script):

    print()
    print("=" * 70)
    print(f"Artist: {artist_name}")
    print(f"Step:   {step_name}")
    print("=" * 70)

    command = [
        sys.executable,
        script,
        artist_name,
    ]

    subprocess.run(
        command,
        check=True,
    )


def main():

    print("=" * 70)
    print("MUSIC ARTIST INSIGHTS — COHORT PIPELINE")
    print("=" * 70)

    for artist_name in ARTISTS:

        for step_name, script in PIPELINE_STEPS:

            try:
                run_step(
                    artist_name,
                    step_name,
                    script,
                )

            except subprocess.CalledProcessError as error:

                print()
                print(
                    f"PIPELINE FAILED: {artist_name}"
                )
                print(
                    f"Failed step: {step_name}"
                )
                print(
                    f"Exit code: {error.returncode}"
                )

                raise

        print()
        print(
            f"✓ Completed pipeline for {artist_name}"
        )

    print()
    print("=" * 70)
    print("COHORT PIPELINE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()