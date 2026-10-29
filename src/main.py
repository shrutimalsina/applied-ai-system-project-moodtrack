"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

try:
    from src.recommender import load_songs, recommend_songs  # python -m src.main
except ImportError:
    from recommender import load_songs, recommend_songs  # python src/main.py


def max_score(user_prefs: dict) -> float:
    """Highest possible score for this profile: 6.5 core + any advanced prefs it sets."""
    total = 6.5
    if user_prefs.get("target_popularity") is not None:
        total += 0.5
    if user_prefs.get("favorite_decade") is not None:
        total += 0.5
    if user_prefs.get("mood_tags"):
        total += 1.0
    if user_prefs.get("likes_instrumental") is not None:
        total += 0.5
    return total


def print_table(recommendations: list, best: float) -> None:
    """Print the top songs as an ASCII table, one reason per line in the Reasons column."""
    headers = ["#", "Song", "Artist", "Score", "Reasons"]
    rows = []
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        rows.append([str(rank), song["title"], song["artist"],
                     f"{score:.2f}/{best:.1f}", explanation.split(", ")])

    widths = [max(len(headers[i]), *(len(row[i]) for row in rows)) for i in range(4)]
    widths.append(max(len(headers[4]), *(len(r) for row in rows for r in row[4])))
    border = "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def line(cells):
        return "| " + " | ".join(c.ljust(w) for c, w in zip(cells, widths)) + " |"

    print(border)
    print(line(headers))
    print(border.replace("-", "="))
    for row in rows:
        reasons = row[4]
        print(line(row[:4] + [reasons[0]]))
        for reason in reasons[1:]:
            print(line(["", "", "", "", reason]))
        print(border)


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # Contrasting taste profiles to check the recommender tells styles apart.
    # likes_acoustic: False -> target acousticness 0.2, True -> 0.8
    profiles = {
        # Upbeat pop fan who wants happy, energetic, non-acoustic songs
        "Happy Pop": {
            "favorite_genre": "pop",
            "favorite_mood": "happy",
            "target_energy": 0.8,
            "target_valence": 0.8,
            "likes_acoustic": False,
            # Advanced prefs: likes current hits, no explicit lyrics
            "target_popularity": 85,
            "favorite_decade": 2020,
            "mood_tags": ["uplifting", "sunny"],
            "likes_instrumental": False,
            "allow_explicit": False,
        },
        # Rock fan who wants loud, intense, darker songs
        "Intense Rock": {
            "favorite_genre": "rock",
            "favorite_mood": "intense",
            "target_energy": 0.9,
            "target_valence": 0.45,
            "likes_acoustic": False,
            # Advanced prefs: 2000s rock sound, aggressive and driving
            "target_popularity": 60,
            "favorite_decade": 2000,
            "mood_tags": ["aggressive", "driving"],
            "likes_instrumental": False,
        },
        # Lofi fan who wants calm, soft, acoustic songs
        "Chill Lofi": {
            "favorite_genre": "lofi",
            "favorite_mood": "chill",
            "target_energy": 0.35,
            "target_valence": 0.6,
            "likes_acoustic": True,
            # Advanced prefs: lesser-known, cozy, mostly instrumental study music
            "target_popularity": 50,
            "favorite_decade": 2010,
            "mood_tags": ["cozy", "calm"],
            "likes_instrumental": True,
        },
    }

    # Adversarial / edge-case profiles meant to "trick" the scoring logic.
    # They set no advanced prefs, so they only use the 5 core features.
    adversarial_profiles = {
        # Conflicting prefs: very high energy but a sad mood
        "Sad Raver (conflict)": {
            "favorite_genre": "edm",
            "favorite_mood": "melancholy",
            "target_energy": 0.9,
            "target_valence": 0.2,
            "likes_acoustic": False,
        },
        # Genre that is not in the catalog, so genre points never apply
        "Unknown Genre (k-pop)": {
            "favorite_genre": "k-pop",
            "favorite_mood": "happy",
            "target_energy": 0.7,
            "target_valence": 0.8,
            "likes_acoustic": False,
        },
        # Capitalized genre/mood: exact string match may silently fail
        "Case Mismatch (Pop/Happy)": {
            "favorite_genre": "Pop",
            "favorite_mood": "Happy",
            "target_energy": 0.8,
            "target_valence": 0.8,
            "likes_acoustic": False,
        },
        # Energy outside the 0-1 range
        "Out-of-Range Energy (1.5)": {
            "favorite_genre": "metal",
            "favorite_mood": "angry",
            "target_energy": 1.5,
            "target_valence": 0.2,
            "likes_acoustic": False,
        },
        # Wants sad, acoustic pop, but every pop song in the catalog is upbeat
        "Sad Acoustic Pop (conflict)": {
            "favorite_genre": "pop",
            "favorite_mood": "melancholy",
            "target_energy": 0.3,
            "target_valence": 0.1,
            "likes_acoustic": True,
        },
    }
    profiles.update(adversarial_profiles)

    for name, user_prefs in profiles.items():
        recommendations = recommend_songs(user_prefs, songs, k=5)

        print()
        print("=" * 60)
        print(f"  Top {len(recommendations)} for: {name}")
        print(f"  (genre={user_prefs['favorite_genre']}, mood={user_prefs['favorite_mood']}, "
              f"energy={user_prefs['target_energy']})")
        print("=" * 60)
        print_table(recommendations, max_score(user_prefs))


if __name__ == "__main__":
    main()
