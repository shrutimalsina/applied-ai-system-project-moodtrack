import pandas as pd

from src.prepare_data import clean, label_mood


def make_row(track_id, name, artist, genre, popularity=50, valence=0.7, energy=0.7,
             tempo=120.0, speechiness=0.05):
    return {
        "Unnamed: 0": 0, "track_id": track_id, "artists": artist, "album_name": "Album",
        "track_name": name, "popularity": popularity, "duration_ms": 200000,
        "explicit": False, "danceability": 0.5, "energy": energy, "key": 0,
        "loudness": -6.0, "mode": 1, "speechiness": speechiness, "acousticness": 0.3,
        "instrumentalness": 0.0, "liveness": 0.1, "valence": valence, "tempo": tempo,
        "time_signature": 4, "track_genre": genre,
    }


def test_label_mood_covers_all_four_quadrants():
    assert label_mood(valence=0.8, energy=0.8) == "happy"
    assert label_mood(valence=0.8, energy=0.2) == "peaceful"
    assert label_mood(valence=0.2, energy=0.8) == "intense"
    assert label_mood(valence=0.2, energy=0.2) == "melancholy"


def test_clean_merges_duplicate_ids_and_keeps_all_genres():
    raw = pd.DataFrame([
        make_row("a", "Song A", "Artist", "pop"),
        make_row("a", "Song A", "Artist", "dance"),
    ])
    out = clean(raw)
    assert len(out) == 1
    assert out.iloc[0]["genres"] == "dance;pop"


def test_clean_keeps_most_popular_rerelease():
    raw = pd.DataFrame([
        make_row("a", "Song A", "Artist", "pop", popularity=10),
        make_row("b", "song a ", "artist", "pop", popularity=90),
    ])
    out = clean(raw)
    assert len(out) == 1
    assert out.iloc[0]["track_id"] == "b"


def test_clean_drops_bad_rows():
    raw = pd.DataFrame([
        make_row("ok", "Good Song", "Artist", "pop"),
        make_row("t0", "No Beat", "Artist", "pop", tempo=0),
        make_row("talk", "Podcast", "Artist", "comedy", speechiness=0.9),
        make_row("na", None, "Artist", "pop"),
    ])
    out = clean(raw)
    assert out["track_id"].tolist() == ["ok"]
