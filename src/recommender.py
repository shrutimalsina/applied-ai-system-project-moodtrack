import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    target_valence: float = 0.5

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k Song objects for the user, using the same scoring as recommend_songs."""
        by_id = {song.id: song for song in self.songs}
        ranked = recommend_songs(asdict(user), [asdict(song) for song in self.songs], k)
        return [by_id[song["id"]] for song, _, _ in ranked]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a readable list of the reasons behind a song's score."""
        score, reasons = score_song(asdict(user), asdict(song))
        return f"Score {score:.2f}: " + ", ".join(reasons)

def load_songs(csv_path: str) -> List[Dict]:
    """Read songs.csv into a list of dicts, converting numeric columns to int/float."""
    int_fields = {"id"}
    float_fields = {"energy", "tempo_bpm", "valence", "danceability", "acousticness"}

    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for key in int_fields:
                row[key] = int(row[key])
            for key in float_fields:
                row[key] = float(row[key])
            songs.append(row)
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score a song (+2.0 genre, +1.5 mood, up to +1.5 energy, +1.0 valence, +0.5 acoustic) and return (score, reasons)."""
    score = 0.0
    reasons = []

    if song["genre"] == user_prefs["favorite_genre"]:
        score += 2.0
        reasons.append("genre match (+2.0)")

    if song["mood"] == user_prefs["favorite_mood"]:
        score += 1.5
        reasons.append("mood match (+1.5)")

    # Closer numeric features earn more points, up to the weight for an exact match
    energy_points = 1.5 * (1 - abs(song["energy"] - user_prefs["target_energy"]))
    score += energy_points
    reasons.append(f"energy similarity (+{energy_points:.2f})")

    valence_points = 1.0 * (1 - abs(song["valence"] - user_prefs.get("target_valence", 0.5)))
    score += valence_points
    reasons.append(f"valence similarity (+{valence_points:.2f})")

    # likes_acoustic: True -> target 0.8, False -> target 0.2
    target_acoustic = 0.8 if user_prefs["likes_acoustic"] else 0.2
    acoustic_points = 0.5 * (1 - abs(song["acousticness"] - target_acoustic))
    score += acoustic_points
    reasons.append(f"acousticness similarity (+{acoustic_points:.2f})")

    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score every song, sort highest first (ties by closer energy), and return the top k."""
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        scored.append((song, score, ", ".join(reasons)))

    # Highest score first; ties go to the song with closer energy
    ranked = sorted(
        scored,
        key=lambda item: (item[1], -abs(item[0]["energy"] - user_prefs["target_energy"])),
        reverse=True,
    )
    return ranked[:k]
