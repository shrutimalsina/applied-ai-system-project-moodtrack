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
        },
        # Rock fan who wants loud, intense, darker songs
        "Intense Rock": {
            "favorite_genre": "rock",
            "favorite_mood": "intense",
            "target_energy": 0.9,
            "target_valence": 0.45,
            "likes_acoustic": False,
        },
        # Lofi fan who wants calm, soft, acoustic songs
        "Chill Lofi": {
            "favorite_genre": "lofi",
            "favorite_mood": "chill",
            "target_energy": 0.35,
            "target_valence": 0.6,
            "likes_acoustic": True,
        },
    }

    # Adversarial / edge-case profiles meant to "trick" the scoring logic
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
        for rank, (song, score, explanation) in enumerate(recommendations, start=1):
            print(f"{rank}. {song['title']} by {song['artist']}")
            print(f"   Score: {score:.2f} / 6.50")
            for reason in explanation.split(", "):
                print(f"   - {reason}")
            print()


if __name__ == "__main__":
    main()
