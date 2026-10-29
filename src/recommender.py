import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict, field

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
    # Advanced features (defaults keep older code and tests working)
    popularity: int = 50
    release_decade: int = 2010
    mood_tags: List[str] = field(default_factory=list)
    instrumentalness: float = 0.0
    explicit: bool = False

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
    # Optional advanced preferences: None means "no preference", so no points
    target_popularity: Optional[int] = None
    favorite_decade: Optional[int] = None
    mood_tags: Optional[List[str]] = None
    likes_instrumental: Optional[bool] = None
    allow_explicit: bool = True

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
    int_fields = {"id", "popularity", "release_decade"}
    float_fields = {"energy", "tempo_bpm", "valence", "danceability", "acousticness", "instrumentalness"}

    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for key in int_fields:
                row[key] = int(row[key])
            for key in float_fields:
                row[key] = float(row[key])
            row["mood_tags"] = row["mood_tags"].split(";") if row["mood_tags"] else []
            row["explicit"] = row["explicit"].strip().lower() == "true"
            songs.append(row)
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score a song and return (score, reasons).

    Core: +2.0 genre, +1.5 mood, up to +1.5 energy, +1.0 valence, +0.5 acoustic.
    Advanced (only if the user sets them): up to +0.5 popularity, +0.5 decade,
    +1.0 mood tags, +0.5 instrumental, and -1.0 for explicit songs if not allowed.
    """
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

    # --- Advanced features: skipped when the user has no preference ---
    if user_prefs.get("target_popularity") is not None:
        gap = abs(song.get("popularity", 50) - user_prefs["target_popularity"]) / 100
        popularity_points = 0.5 * (1 - gap)
        score += popularity_points
        reasons.append(f"popularity similarity (+{popularity_points:.2f})")

    if user_prefs.get("favorite_decade") is not None:
        decade_gap = abs(song.get("release_decade", 2010) - user_prefs["favorite_decade"])
        if decade_gap == 0:
            score += 0.5
            reasons.append("same decade (+0.5)")
        elif decade_gap == 10:
            score += 0.25
            reasons.append("nearby decade (+0.25)")

    if user_prefs.get("mood_tags"):
        shared = [tag for tag in song.get("mood_tags", []) if tag in user_prefs["mood_tags"]]
        tag_points = min(0.5 * len(shared), 1.0)
        if shared:
            score += tag_points
            reasons.append(f"mood tags {'/'.join(shared)} (+{tag_points:.1f})")

    if user_prefs.get("likes_instrumental") is not None:
        target_instrumental = 0.8 if user_prefs["likes_instrumental"] else 0.2
        instrumental_points = 0.5 * (1 - abs(song.get("instrumentalness", 0.0) - target_instrumental))
        score += instrumental_points
        reasons.append(f"instrumental similarity (+{instrumental_points:.2f})")

    if not user_prefs.get("allow_explicit", True) and song.get("explicit", False):
        score -= 1.0
        reasons.append("explicit content (-1.0)")

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
