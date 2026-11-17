import pandas as pd
import pytest

import src.agent as agent
from src.agent import build_playlist, critic, plan_path
from src.catalog import Catalog
from src.mood import correct_mood


def song(id, valence, energy, explicit=False, artist=None):
    return {
        "id": id, "track_id": f"t{id}", "title": f"Song {id}", "artist": artist or f"Artist {id}",
        "album": "Album", "genre": "pop", "genres": "pop", "mood": "happy",
        "energy": energy, "valence": valence, "tempo_bpm": 120, "danceability": 0.5,
        "acousticness": 0.3, "instrumentalness": 0.0, "speechiness": 0.05,
        "loudness": -6.0, "mode": 1, "popularity": 50, "explicit": explicit,
        "duration_ms": 200000,
    }


@pytest.fixture
def catalog(tmp_path):
    # A grid of songs covering the whole mood map
    rows, n = [], 0
    for v in range(0, 21):
        for e in range(0, 21):
            n += 1
            rows.append(song(n, v / 20, e / 20))
    path = tmp_path / "catalog.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return Catalog(path)


def test_plan_starts_at_current_mood_and_ends_at_goal():
    path = plan_path((0.1, 0.3), (0.7, 0.5), steps=5)
    assert path[0] == (0.1, 0.3)
    assert path[-1] == (0.7, 0.5)
    assert len(path) == 5


def test_playlist_moves_toward_goal(catalog):
    result = build_playlist(catalog, correct_mood("sadness"), "lift", save_trace=False)
    assert result.passed
    assert len(result.songs) == 5
    assert result.songs[-1]["valence"] > result.songs[0]["valence"]
    assert all(s["why"] for s in result.songs)


def test_critic_catches_explicit_song_for_sad_user(catalog):
    reading = correct_mood("sadness")
    path = plan_path((reading.valence, reading.energy), (0.7, 0.5))
    songs = [song(1000 + i, v, e) for i, (v, e) in enumerate(path)]
    songs[2]["explicit"] = True
    problems = critic(songs, path, path[-1], reading, True, catalog)
    assert ("explicit_when_fragile", 2) in problems


def test_critic_catches_song_moving_away_from_goal(catalog):
    reading = correct_mood("sadness")
    path = plan_path((0.15, 0.25), (0.7, 0.5))
    songs = [song(i + 1, v, e) for i, (v, e) in enumerate(path)]
    songs[3] = song(99, 0.1, 0.2)  # jumps back to very sad near the end
    kinds = [kind for kind, _ in critic(songs, path, path[-1], reading, True, catalog)]
    assert "moves_away_from_goal" in kinds


def test_agent_fixes_explicit_problem_and_retries(tmp_path):
    # Only explicit songs near the sad starting point, clean songs elsewhere
    rows = [song(1, 0.15, 0.25, explicit=True)]
    rows += [song(10 + i, 0.15 + 0.01 * i, 0.25, artist=f"Clean {i}") for i in range(1, 30)]
    rows += [song(100 + i, v / 10, e / 10) for i, (v, e) in enumerate(
        [(v, e) for v in range(11) for e in range(11)])]
    path = tmp_path / "catalog.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    result = build_playlist(Catalog(path), correct_mood("sadness"), "lift", save_trace=False)
    assert not any(s["explicit"] for s in result.songs)
    assert result.attempts == 2  # first try had the explicit song, second try fixed it
    assert any(line.startswith("FIX") for line in result.trace)


def test_trace_is_saved_without_journal_text(catalog, tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "TRACE_DIR", tmp_path / "traces")
    result = build_playlist(catalog, correct_mood("anger"), "calm")
    text = result.trace_file.read_text()
    assert "PLAN" in text and "CHECK" in text and "RESULT" in text
