"""Clean the raw Kaggle Spotify Tracks dataset and label every song with a mood.

Run from the project root:
    python -m src.prepare_data

Reads:  data/raw/spotify-tracks-dataset.csv   (original Kaggle download, untouched)
Writes: data/tracks_clean.csv                  (deduplicated, mood-labeled catalog)

How moods are labeled: every song has two Spotify numbers from 0 to 1.
  - valence: how positive the song sounds (0 = sad, 1 = happy)
  - energy:  how intense the song feels  (0 = calm, 1 = loud and fast)
Splitting both in half gives four moods:

                  calm (energy < 0.5)   energetic (energy >= 0.5)
  positive        peaceful              happy
  negative        melancholy            intense

This idea comes from a psychology model of emotions (Russell, 1980).
"""

import argparse
import logging
from pathlib import Path

import pandas as pd

RAW_PATH = Path("data/raw/spotify-tracks-dataset.csv")
CLEAN_PATH = Path("data/tracks_clean.csv")

# Songs above this are mostly talking (podcasts, comedy, spoken word), not music
MAX_SPEECHINESS = 0.66

log = logging.getLogger("prepare_data")


def label_mood(valence: float, energy: float) -> str:
    """Turn a song's valence and energy into one of four mood words."""
    if valence >= 0.5:
        return "happy" if energy >= 0.5 else "peaceful"
    return "intense" if energy >= 0.5 else "melancholy"


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    """Return a cleaned copy of the raw dataset, logging what each step removes."""
    df = raw.copy()
    log.info("Loaded %d rows", len(df))

    # 1. Drop leftover pandas index columns from the Kaggle export
    df = df.drop(columns=[c for c in df.columns if c == "" or c.startswith("Unnamed")])

    # 2. Rows missing a title or artist can't be shown to a user
    before = len(df)
    df = df.dropna(subset=["track_name", "artists"])
    log.info("Removed %d rows with missing title/artist", before - len(df))

    # 3. Bad audio analysis: tempo 0 means Spotify couldn't detect a beat
    before = len(df)
    df = df[df["tempo"] > 0]
    log.info("Removed %d rows with tempo = 0", before - len(df))

    # 4. Spoken-word tracks aren't songs
    before = len(df)
    df = df[df["speechiness"] <= MAX_SPEECHINESS]
    log.info("Removed %d spoken-word rows (speechiness > %.2f)", before - len(df), MAX_SPEECHINESS)

    # 5. Same track_id listed under several genres: keep one row, but remember every genre
    genres_per_track = df.groupby("track_id")["track_genre"].agg(lambda g: ";".join(sorted(set(g))))
    before = len(df)
    df = df.drop_duplicates(subset="track_id", keep="first").copy()
    df["genres"] = df["track_id"].map(genres_per_track)
    log.info("Merged %d duplicate track_id rows (genres kept in 'genres' column)", before - len(df))

    # 6. Same song re-released with a new track_id (singles, albums, compilations):
    #    keep the most popular version
    before = len(df)
    df["_key"] = df["track_name"].str.strip().str.lower() + "|" + df["artists"].str.strip().str.lower()
    df = df.sort_values("popularity", ascending=False).drop_duplicates(subset="_key", keep="first")
    df = df.drop(columns="_key")
    log.info("Removed %d re-released copies of the same title + artist", before - len(df))

    # 7. Derive the mood label the recommender matches on
    df["mood"] = [label_mood(v, e) for v, e in zip(df["valence"], df["energy"])]

    # 8. Rename to the column names the original recommender uses
    df = df.rename(columns={
        "track_name": "title",
        "artists": "artist",
        "album_name": "album",
        "track_genre": "genre",
        "tempo": "tempo_bpm",
    })
    df["artist"] = df["artist"].str.replace(";", ", ")  # "A;B" -> "A, B" for display
    df["explicit"] = df["explicit"].astype(str).str.lower() == "true"

    df = df.sort_values("track_id").reset_index(drop=True)
    df.insert(0, "id", range(1, len(df) + 1))

    columns = [
        "id", "track_id", "title", "artist", "album", "genre", "genres", "mood",
        "energy", "valence", "tempo_bpm", "danceability", "acousticness",
        "instrumentalness", "speechiness", "loudness", "mode", "popularity",
        "explicit", "duration_ms",
    ]
    log.info("Kept %d unique songs (%.1f%% of raw rows)", len(df), 100 * len(df) / len(raw))
    return df[columns]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw", type=Path, default=RAW_PATH)
    parser.add_argument("--out", type=Path, default=CLEAN_PATH)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if not args.raw.exists():
        raise SystemExit(
            f"Raw dataset not found at {args.raw}.\n"
            "Download 'Spotify Tracks Dataset' from Kaggle and unzip it into data/raw/ (see README)."
        )

    tracks = clean(pd.read_csv(args.raw))
    tracks.to_csv(args.out, index=False)

    log.info("\nMood distribution:\n%s", tracks["mood"].value_counts().to_string())
    log.info("\nWrote %s", args.out)


if __name__ == "__main__":
    main()
