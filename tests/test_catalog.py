import pandas as pd
import pytest

from src.catalog import Catalog


def song(id, valence, energy, artist="Artist", genre="pop", explicit=False, popularity=50):
    return {
        "id": id, "track_id": f"t{id}", "title": f"Song {id}", "artist": artist,
        "album": "Album", "genre": genre, "genres": genre, "mood": "happy",
        "energy": energy, "valence": valence, "tempo_bpm": 120, "danceability": 0.5,
        "acousticness": 0.3, "instrumentalness": 0.0, "speechiness": 0.05,
        "loudness": -6.0, "mode": 1, "popularity": popularity, "explicit": explicit,
        "duration_ms": 200000,
    }


@pytest.fixture
def catalog(tmp_path):
    # 30 songs spread along the diagonal, plus a few special cases
    rows = [song(i, valence=i / 30, energy=i / 30) for i in range(1, 31)]
    rows.append(song(100, valence=0.5, energy=0.5, explicit=True))
    rows.append(song(101, valence=0.5, energy=0.5, popularity=5))
    path = tmp_path / "catalog.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return Catalog(path)


def test_retrieve_returns_closest_songs_first(catalog):
    hits = catalog.retrieve(valence=0.5, energy=0.5, radius=0.5, limit=3)
    assert abs(hits[0]["valence"] - 0.5) < 0.02


def test_retrieve_respects_filters(catalog):
    ids = [s["id"] for s in catalog.retrieve(0.5, 0.5, radius=0.5, allow_explicit=False, exclude_ids=[15])]
    assert 100 not in ids  # explicit
    assert 101 not in ids  # below min popularity
    assert 15 not in ids   # excluded


def test_retrieve_widens_radius_instead_of_returning_nothing(catalog):
    # Nothing is within 0.01 of this corner, but the search should still find songs
    assert len(catalog.retrieve(valence=0.0, energy=1.0, radius=0.01)) > 0


def test_recommend_uses_original_scorer(catalog):
    top = catalog.recommend(0.5, 0.5, k=2, radius=0.5)
    assert len(top) == 2
    assert top[0]["score"] >= top[1]["score"]
    assert "energy similarity" in top[0]["reasons"]
