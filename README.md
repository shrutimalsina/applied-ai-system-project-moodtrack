# 🎵 Music Recommender Simulation

## Project Summary

This project is a small music recommender. A user describes their taste (favorite genre, mood, energy level, how happy they want songs to sound, and whether they like acoustic music). The program gives every song in a 23-song catalog a score based on how well it matches, then shows the top 5 songs with a short reason for each score.

I also tested it with "tricky" user profiles to see where the scoring breaks or gives strange results.

---

## How The System Works

This is a content-based recommender. It suggests songs by comparing what each song is like to what the user says they like. It does not use other users' data.

### Song features

Each `Song` has many attributes, but the recommender uses only these 5:

| Feature | Type | What it means |
|---|---|---|
| `genre` | category | Style of music (pop, lofi, rock...) |
| `mood` | category | Feeling of the song (happy, chill, intense...) |
| `energy` | 0 to 1 | Calm (0) to powerful (1) |
| `valence` | 0 to 1 | Sad or dark (0) to happy (1) |
| `acousticness` | 0 to 1 | Electronic (0) to acoustic (1) |

`tempo_bpm` and `danceability` are not used because they mostly rise and fall with `energy`, so they dont add much new information.

### What the UserProfile stores

- `favorite_genre`: the genre the user likes most (e.g. "pop")
- `favorite_mood`: the mood they want right now (e.g. "happy")
- `target_energy`: how energetic they want songs to be (0 to 1)
- `target_valence`: how happy they want songs to sound (0 to 1)
- `likes_acoustic`: yes/no. Yes means a target acousticness of 0.8, and no means 0.2.

### How a song gets a score (Scoring Rule)

1. **Categories (match or not):** the song gets 1 if it matches the user's choice and 0 if it doesn't.
2. **Numbers (closeness):** the song gets more points the closer it is to the user's target. It does not get more points just for having a higher value.

   ```
   closeness = 1 - |song value - user target|
   ```

   An exact match gives 1.0, and a song that is very far away gives close to 0.
3. **Weights:** each feature is multiplied by how important it is, and the results are added up.

```
score = 2.0 × genre match
      + 1.5 × mood match
      + 1.5 × energy closeness
      + 1.0 × valence closeness
      + 0.5 × acousticness closeness
```

The highest possible score is **6.5**. Genre has the biggest weight because it reflects long-term taste, while mood changes from day to day.

**Example:** a user wants pop, happy, energy 0.8, valence 0.8 and not acoustic.

- *Sunrise City* (pop, happy) scores **6.42**, a strong match.
- *Library Rain* (lofi, chill) scores **1.80**, a weak match.

### Advanced features (optional)

Each song also has 5 extra attributes in `songs.csv`. They only count if the user sets the matching preference, so profiles without them score exactly as before.

| Song feature | User preference | Points |
|---|---|---|
| `popularity` (0 to 100) | `target_popularity` | up to +0.5, closer is better |
| `release_decade` (e.g. 2010) | `favorite_decade` | +0.5 same decade, +0.25 next decade |
| `mood_tags` (e.g. "cozy;rainy") | `mood_tags` list | +0.5 per shared tag, max +1.0 |
| `instrumentalness` (0 to 1) | `likes_instrumental` yes/no | up to +0.5 (target 0.8 or 0.2) |
| `explicit` (true/false) | `allow_explicit` | -1.0 if explicit and not allowed |

With every advanced preference set, the highest possible score is **9.0**. Results are shown as a table that lists the reasons for each score.

### How songs are chosen (Ranking Rule)

1. Score every song in the catalog.
2. Sort the songs from highest score to lowest.
3. If two songs have the same score, the one with closer energy goes first.
4. Return the **top 5** songs, each with a short reason (e.g. "matches your genre, similar energy").

```
User profile + songs.csv
        ↓
Score each song (Scoring Rule)
        ↓
Sort by score (Ranking Rule)
        ↓
Top 5 recommendations + reasons
```

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Run with `python -m src.main`. The first three are normal profiles that also use the [advanced features](#advanced-features-optional). The rest are adversarial / edge-case profiles designed to trick the scoring logic. They only use the 5 core features, so their highest possible score is 6.5.

### Happy Pop

Works as expected: pop + happy songs on top. With the advanced prefs (no explicit songs, "uplifting/sunny" tags), Gym Hero drops to #5 and the happy indie pop song Rooftop Lights moves up to #3.

```
============================================================
  Top 5 for: Happy Pop
  (genre=pop, mood=happy, energy=0.8)
============================================================
+---+-------------------+---------------+----------+----------------------------------+
| # | Song              | Artist        | Score    | Reasons                          |
+===+===================+===============+==========+==================================+
| 1 | Sunrise City      | Neon Echo     | 8.85/9.0 | genre match (+2.0)               |
|   |                   |               |          | mood match (+1.5)                |
|   |                   |               |          | energy similarity (+1.47)        |
|   |                   |               |          | valence similarity (+0.96)       |
|   |                   |               |          | acousticness similarity (+0.49)  |
|   |                   |               |          | popularity similarity (+0.50)    |
|   |                   |               |          | same decade (+0.5)               |
|   |                   |               |          | mood tags uplifting/sunny (+1.0) |
|   |                   |               |          | instrumental similarity (+0.42)  |
+---+-------------------+---------------+----------+----------------------------------+
| 2 | Golden Hour Crush | Lila Bright   | 8.15/9.0 | genre match (+2.0)               |
|   |                   |               |          | mood match (+1.5)                |
|   |                   |               |          | energy similarity (+1.38)        |
|   |                   |               |          | valence similarity (+0.90)       |
|   |                   |               |          | acousticness similarity (+0.47)  |
|   |                   |               |          | popularity similarity (+0.47)    |
|   |                   |               |          | same decade (+0.5)               |
|   |                   |               |          | mood tags uplifting (+0.5)       |
|   |                   |               |          | instrumental similarity (+0.42)  |
+---+-------------------+---------------+----------+----------------------------------+
| 3 | Rooftop Lights    | Indigo Parade | 6.49/9.0 | mood match (+1.5)                |
|   |                   |               |          | energy similarity (+1.44)        |
|   |                   |               |          | valence similarity (+0.99)       |
|   |                   |               |          | acousticness similarity (+0.43)  |
|   |                   |               |          | popularity similarity (+0.43)    |
|   |                   |               |          | nearby decade (+0.25)            |
|   |                   |               |          | mood tags uplifting/sunny (+1.0) |
|   |                   |               |          | instrumental similarity (+0.45)  |
+---+-------------------+---------------+----------+----------------------------------+
| 4 | Bassline Sunrise  | Pulse Theory  | 6.07/9.0 | mood match (+1.5)                |
|   |                   |               |          | energy similarity (+1.38)        |
|   |                   |               |          | valence similarity (+0.97)       |
|   |                   |               |          | acousticness similarity (+0.42)  |
|   |                   |               |          | popularity similarity (+0.45)    |
|   |                   |               |          | same decade (+0.5)               |
|   |                   |               |          | mood tags sunny (+0.5)           |
|   |                   |               |          | instrumental similarity (+0.35)  |
+---+-------------------+---------------+----------+----------------------------------+
| 5 | Gym Hero          | Max Pulse     | 5.10/9.0 | genre match (+2.0)               |
|   |                   |               |          | energy similarity (+1.30)        |
|   |                   |               |          | valence similarity (+0.97)       |
|   |                   |               |          | acousticness similarity (+0.42)  |
|   |                   |               |          | popularity similarity (+0.48)    |
|   |                   |               |          | same decade (+0.5)               |
|   |                   |               |          | instrumental similarity (+0.41)  |
|   |                   |               |          | explicit content (-1.0)          |
+---+-------------------+---------------+----------+----------------------------------+
```

### Intense Rock

Only one rock song exists, so other intense songs fill the list. The "aggressive" mood tag pulls in the metal song Iron Verdict at #4.

```
============================================================
  Top 5 for: Intense Rock
  (genre=rock, mood=intense, energy=0.9)
============================================================
+---+-------------------+--------------+----------+-------------------------------------+
| # | Song              | Artist       | Score    | Reasons                             |
+===+===================+==============+==========+=====================================+
| 1 | Storm Runner      | Voltline     | 8.86/9.0 | genre match (+2.0)                  |
|   |                   |              |          | mood match (+1.5)                   |
|   |                   |              |          | energy similarity (+1.48)           |
|   |                   |              |          | valence similarity (+0.97)          |
|   |                   |              |          | acousticness similarity (+0.45)     |
|   |                   |              |          | popularity similarity (+0.45)       |
|   |                   |              |          | same decade (+0.5)                  |
|   |                   |              |          | mood tags aggressive/driving (+1.0) |
|   |                   |              |          | instrumental similarity (+0.50)     |
+---+-------------------+--------------+----------+-------------------------------------+
| 2 | Pit Storm         | Grave Signal | 5.97/9.0 | mood match (+1.5)                   |
|   |                   |              |          | energy similarity (+1.44)           |
|   |                   |              |          | valence similarity (+0.90)          |
|   |                   |              |          | acousticness similarity (+0.42)     |
|   |                   |              |          | popularity similarity (+0.46)       |
|   |                   |              |          | nearby decade (+0.25)               |
|   |                   |              |          | mood tags aggressive (+0.5)         |
|   |                   |              |          | instrumental similarity (+0.50)     |
+---+-------------------+--------------+----------+-------------------------------------+
| 3 | Gym Hero          | Max Pulse    | 5.33/9.0 | mood match (+1.5)                   |
|   |                   |              |          | energy similarity (+1.46)           |
|   |                   |              |          | valence similarity (+0.68)          |
|   |                   |              |          | acousticness similarity (+0.42)     |
|   |                   |              |          | popularity similarity (+0.36)       |
|   |                   |              |          | mood tags aggressive (+0.5)         |
|   |                   |              |          | instrumental similarity (+0.41)     |
+---+-------------------+--------------+----------+-------------------------------------+
| 4 | Iron Verdict      | Grave Signal | 4.25/9.0 | energy similarity (+1.40)           |
|   |                   |              |          | valence similarity (+0.77)          |
|   |                   |              |          | acousticness similarity (+0.41)     |
|   |                   |              |          | popularity similarity (+0.44)       |
|   |                   |              |          | nearby decade (+0.25)               |
|   |                   |              |          | mood tags aggressive (+0.5)         |
|   |                   |              |          | instrumental similarity (+0.47)     |
+---+-------------------+--------------+----------+-------------------------------------+
| 5 | Late Night Cipher | Kid Static   | 3.62/9.0 | energy similarity (+1.08)           |
|   |                   |              |          | valence similarity (+0.95)          |
|   |                   |              |          | acousticness similarity (+0.46)     |
|   |                   |              |          | popularity similarity (+0.46)       |
|   |                   |              |          | nearby decade (+0.25)               |
|   |                   |              |          | instrumental similarity (+0.41)     |
+---+-------------------+--------------+----------+-------------------------------------+
```

### Chill Lofi

Works as expected: all three lofi songs rank first. The "cozy" tag and liking instrumental music boost the lofi songs even more.

```
============================================================
  Top 5 for: Chill Lofi
  (genre=lofi, mood=chill, energy=0.35)
============================================================
+---+---------------------+----------------+----------+---------------------------------+
| # | Song                | Artist         | Score    | Reasons                         |
+===+=====================+================+==========+=================================+
| 1 | Library Rain        | Paper Lanterns | 8.38/9.0 | genre match (+2.0)              |
|   |                     |                |          | mood match (+1.5)               |
|   |                     |                |          | energy similarity (+1.50)       |
|   |                     |                |          | valence similarity (+1.00)      |
|   |                     |                |          | acousticness similarity (+0.47) |
|   |                     |                |          | popularity similarity (+0.47)   |
|   |                     |                |          | same decade (+0.5)              |
|   |                     |                |          | mood tags cozy (+0.5)           |
|   |                     |                |          | instrumental similarity (+0.44) |
+---+---------------------+----------------+----------+---------------------------------+
| 2 | Midnight Coding     | LoRoom         | 7.96/9.0 | genre match (+2.0)              |
|   |                     |                |          | mood match (+1.5)               |
|   |                     |                |          | energy similarity (+1.40)       |
|   |                     |                |          | valence similarity (+0.96)      |
|   |                     |                |          | acousticness similarity (+0.45) |
|   |                     |                |          | popularity similarity (+0.45)   |
|   |                     |                |          | nearby decade (+0.25)           |
|   |                     |                |          | mood tags cozy (+0.5)           |
|   |                     |                |          | instrumental similarity (+0.45) |
+---+---------------------+----------------+----------+---------------------------------+
| 3 | Focus Flow          | LoRoom         | 6.58/9.0 | genre match (+2.0)              |
|   |                     |                |          | energy similarity (+1.42)       |
|   |                     |                |          | valence similarity (+0.99)      |
|   |                     |                |          | acousticness similarity (+0.49) |
|   |                     |                |          | popularity similarity (+0.46)   |
|   |                     |                |          | nearby decade (+0.25)           |
|   |                     |                |          | mood tags calm (+0.5)           |
|   |                     |                |          | instrumental similarity (+0.46) |
+---+---------------------+----------------+----------+---------------------------------+
| 4 | Spacewalk Thoughts  | Orbit Bloom    | 5.66/9.0 | mood match (+1.5)               |
|   |                     |                |          | energy similarity (+1.40)       |
|   |                     |                |          | valence similarity (+0.95)      |
|   |                     |                |          | acousticness similarity (+0.44) |
|   |                     |                |          | popularity similarity (+0.45)   |
|   |                     |                |          | same decade (+0.5)              |
|   |                     |                |          | instrumental similarity (+0.43) |
+---+---------------------+----------------+----------+---------------------------------+
| 5 | Coffee Shop Stories | Slow Stereo    | 4.24/9.0 | energy similarity (+1.47)       |
|   |                     |                |          | valence similarity (+0.89)      |
|   |                     |                |          | acousticness similarity (+0.46) |
|   |                     |                |          | popularity similarity (+0.47)   |
|   |                     |                |          | mood tags cozy (+0.5)           |
|   |                     |                |          | instrumental similarity (+0.45) |
+---+---------------------+----------------+----------+---------------------------------+
```

### Sad Raver (conflict)

Genre (+2.0) beats mood (+1.5), so upbeat, happy EDM wins even though the user asked for melancholy.

```
============================================================
  Top 5 for: Sad Raver (conflict)
  (genre=edm, mood=melancholy, energy=0.9)
============================================================
+---+------------------+--------------+----------+---------------------------------+
| # | Song             | Artist       | Score    | Reasons                         |
+===+==================+==============+==========+=================================+
| 1 | Bassline Sunrise | Pulse Theory | 4.26/6.5 | genre match (+2.0)              |
|   |                  |              |          | energy similarity (+1.47)       |
|   |                  |              |          | valence similarity (+0.37)      |
|   |                  |              |          | acousticness similarity (+0.42) |
+---+------------------+--------------+----------+---------------------------------+
| 2 | Neon Euphoria    | Pulse Theory | 4.16/6.5 | genre match (+2.0)              |
|   |                  |              |          | energy similarity (+1.43)       |
|   |                  |              |          | valence similarity (+0.32)      |
|   |                  |              |          | acousticness similarity (+0.41) |
+---+------------------+--------------+----------+---------------------------------+
| 3 | Paper Boats      | Hollow Pines | 3.20/6.5 | mood match (+1.5)               |
|   |                  |              |          | energy similarity (+0.60)       |
|   |                  |              |          | valence similarity (+0.95)      |
|   |                  |              |          | acousticness similarity (+0.15) |
+---+------------------+--------------+----------+---------------------------------+
| 4 | Winter Strings   | Elena Marsh  | 3.07/6.5 | mood match (+1.5)               |
|   |                  |              |          | energy similarity (+0.52)       |
|   |                  |              |          | valence similarity (+0.92)      |
|   |                  |              |          | acousticness similarity (+0.12) |
+---+------------------+--------------+----------+---------------------------------+
| 5 | Iron Verdict     | Grave Signal | 2.79/6.5 | energy similarity (+1.40)       |
|   |                  |              |          | valence similarity (+0.98)      |
|   |                  |              |          | acousticness similarity (+0.41) |
+---+------------------+--------------+----------+---------------------------------+
```

### Unknown Genre (k-pop)

No genre match is possible, so the top score is capped at 4.5 and results fall back to mood + numeric features.

```
============================================================
  Top 5 for: Unknown Genre (k-pop)
  (genre=k-pop, mood=happy, energy=0.7)
============================================================
+---+-------------------+---------------+----------+---------------------------------+
| # | Song              | Artist        | Score    | Reasons                         |
+===+===================+===============+==========+=================================+
| 1 | Golden Hour Crush | Lila Bright   | 4.34/6.5 | mood match (+1.5)               |
|   |                   |               |          | energy similarity (+1.47)       |
|   |                   |               |          | valence similarity (+0.90)      |
|   |                   |               |          | acousticness similarity (+0.47) |
+---+-------------------+---------------+----------+---------------------------------+
| 2 | Rooftop Lights    | Indigo Parade | 4.33/6.5 | mood match (+1.5)               |
|   |                   |               |          | energy similarity (+1.41)       |
|   |                   |               |          | valence similarity (+0.99)      |
|   |                   |               |          | acousticness similarity (+0.43) |
+---+-------------------+---------------+----------+---------------------------------+
| 3 | Sunrise City      | Neon Echo     | 4.27/6.5 | mood match (+1.5)               |
|   |                   |               |          | energy similarity (+1.32)       |
|   |                   |               |          | valence similarity (+0.96)      |
|   |                   |               |          | acousticness similarity (+0.49) |
+---+-------------------+---------------+----------+---------------------------------+
| 4 | Bassline Sunrise  | Pulse Theory  | 4.12/6.5 | mood match (+1.5)               |
|   |                   |               |          | energy similarity (+1.23)       |
|   |                   |               |          | valence similarity (+0.97)      |
|   |                   |               |          | acousticness similarity (+0.42) |
+---+-------------------+---------------+----------+---------------------------------+
| 5 | Island Time       | Sunny Roots   | 2.68/6.5 | energy similarity (+1.35)       |
|   |                   |               |          | valence similarity (+0.95)      |
|   |                   |               |          | acousticness similarity (+0.38) |
+---+-------------------+---------------+----------+---------------------------------+
```

### Case Mismatch (Pop/Happy)

"Pop" != "pop": genre and mood silently never match, so ranking uses only the numeric features (a hip hop song makes the top 5).

```
============================================================
  Top 5 for: Case Mismatch (Pop/Happy)
  (genre=Pop, mood=Happy, energy=0.8)
============================================================
+---+-------------------+---------------+----------+---------------------------------+
| # | Song              | Artist        | Score    | Reasons                         |
+===+===================+===============+==========+=================================+
| 1 | Sunrise City      | Neon Echo     | 2.92/6.5 | energy similarity (+1.47)       |
|   |                   |               |          | valence similarity (+0.96)      |
|   |                   |               |          | acousticness similarity (+0.49) |
+---+-------------------+---------------+----------+---------------------------------+
| 2 | Rooftop Lights    | Indigo Parade | 2.85/6.5 | energy similarity (+1.44)       |
|   |                   |               |          | valence similarity (+0.99)      |
|   |                   |               |          | acousticness similarity (+0.43) |
+---+-------------------+---------------+----------+---------------------------------+
| 3 | Bassline Sunrise  | Pulse Theory  | 2.77/6.5 | energy similarity (+1.38)       |
|   |                   |               |          | valence similarity (+0.97)      |
|   |                   |               |          | acousticness similarity (+0.42) |
+---+-------------------+---------------+----------+---------------------------------+
| 4 | Crown the Block   | Kid Static    | 2.76/6.5 | energy similarity (+1.50)       |
|   |                   |               |          | valence similarity (+0.82)      |
|   |                   |               |          | acousticness similarity (+0.44) |
+---+-------------------+---------------+----------+---------------------------------+
| 5 | Golden Hour Crush | Lila Bright   | 2.75/6.5 | energy similarity (+1.38)       |
|   |                   |               |          | valence similarity (+0.90)      |
|   |                   |               |          | acousticness similarity (+0.47) |
+---+-------------------+---------------+----------+---------------------------------+
```

### Out-of-Range Energy (1.5)

No input check: energy points shrink for every song, but ranking still looks reasonable. Larger values (e.g. 3.0) would give negative points.

```
============================================================
  Top 5 for: Out-of-Range Energy (1.5)
  (genre=metal, mood=angry, energy=1.5)
============================================================
+---+------------------+--------------+----------+---------------------------------+
| # | Song             | Artist       | Score    | Reasons                         |
+===+==================+==============+==========+=================================+
| 1 | Iron Verdict     | Grave Signal | 5.60/6.5 | genre match (+2.0)              |
|   |                  |              |          | mood match (+1.5)               |
|   |                  |              |          | energy similarity (+0.70)       |
|   |                  |              |          | valence similarity (+0.98)      |
|   |                  |              |          | acousticness similarity (+0.41) |
+---+------------------+--------------+----------+---------------------------------+
| 2 | Pit Storm        | Grave Signal | 3.93/6.5 | genre match (+2.0)              |
|   |                  |              |          | energy similarity (+0.66)       |
|   |                  |              |          | valence similarity (+0.85)      |
|   |                  |              |          | acousticness similarity (+0.42) |
+---+------------------+--------------+----------+---------------------------------+
| 3 | Storm Runner     | Voltline     | 1.78/6.5 | energy similarity (+0.61)       |
|   |                  |              |          | valence similarity (+0.72)      |
|   |                  |              |          | acousticness similarity (+0.45) |
+---+------------------+--------------+----------+---------------------------------+
| 4 | Night Drive Loop | Neon Echo    | 1.57/6.5 | energy similarity (+0.38)       |
|   |                  |              |          | valence similarity (+0.71)      |
|   |                  |              |          | acousticness similarity (+0.49) |
+---+------------------+--------------+----------+---------------------------------+
| 5 | Gym Hero         | Max Pulse    | 1.50/6.5 | energy similarity (+0.65)       |
|   |                  |              |          | valence similarity (+0.43)      |
|   |                  |              |          | acousticness similarity (+0.42) |
+---+------------------+--------------+----------+---------------------------------+
```

### Sad Acoustic Pop (conflict)

Every pop song in the catalog is upbeat, so sad acoustic folk/classical songs (mood + valence + acoustic) outrank the genre matches.

```
============================================================
  Top 5 for: Sad Acoustic Pop (conflict)
  (genre=pop, mood=melancholy, energy=0.3)
============================================================
+---+-------------------+--------------+----------+---------------------------------+
| # | Song              | Artist       | Score    | Reasons                         |
+===+===================+==============+==========+=================================+
| 1 | Paper Boats       | Hollow Pines | 4.30/6.5 | mood match (+1.5)               |
|   |                   |              |          | energy similarity (+1.50)       |
|   |                   |              |          | valence similarity (+0.85)      |
|   |                   |              |          | acousticness similarity (+0.45) |
+---+-------------------+--------------+----------+---------------------------------+
| 2 | Winter Strings    | Elena Marsh  | 4.17/6.5 | mood match (+1.5)               |
|   |                   |              |          | energy similarity (+1.42)       |
|   |                   |              |          | valence similarity (+0.82)      |
|   |                   |              |          | acousticness similarity (+0.43) |
+---+-------------------+--------------+----------+---------------------------------+
| 3 | Golden Hour Crush | Lila Bright  | 3.30/6.5 | genre match (+2.0)              |
|   |                   |              |          | energy similarity (+0.87)       |
|   |                   |              |          | valence similarity (+0.20)      |
|   |                   |              |          | acousticness similarity (+0.22) |
+---+-------------------+--------------+----------+---------------------------------+
| 4 | Sunrise City      | Neon Echo    | 3.17/6.5 | genre match (+2.0)              |
|   |                   |              |          | energy similarity (+0.72)       |
|   |                   |              |          | valence similarity (+0.26)      |
|   |                   |              |          | acousticness similarity (+0.19) |
+---+-------------------+--------------+----------+---------------------------------+
| 5 | Gym Hero          | Max Pulse    | 3.01/6.5 | genre match (+2.0)              |
|   |                   |              |          | energy similarity (+0.55)       |
|   |                   |              |          | valence similarity (+0.33)      |
|   |                   |              |          | acousticness similarity (+0.12) |
+---+-------------------+--------------+----------+---------------------------------+
```

---

## Experiments You Tried

**1. Adding valence and acousticness to the score**

At first the score only used genre, mood and energy. A user who wanted *sad, acoustic pop* still got happy, electronic pop songs, because the program ignored those wishes. After adding valence and acousticness, sad acoustic songs (Paper Boats, Winter Strings) moved to the top.

**2. Lowering the genre weight from 2.0 to 0.5**

- *Happy Pop:* barely changed. Sunrise City and Golden Hour Crush stayed on top. Gym Hero (pop but not happy) dropped from #3 to #5.
- *Sad Raver* (EDM fan who wants sad music): changed a lot. With genre at 2.0, happy EDM songs were #1 and #2. With genre at 0.5, sad songs (Paper Boats, Winter Strings) took over.

So the genre weight decides who wins when genre and mood disagree.

**3. Tricky (edge-case) user profiles**

| Profile | What happened |
|---|---|
| Sad Raver (high energy + sad mood) | Genre won, so happy EDM was recommended to a sad user |
| Unknown genre (k-pop) | No song can get genre points, so the best score is only 4.5 out of 6.5 |
| Case mismatch ("Pop" vs "pop") | Genre and mood never matched, with no warning |
| Energy = 1.5 (outside 0 to 1) | Still worked, but every song lost energy points. No input check |
| Sad acoustic pop | All pop songs in the catalog are upbeat, so non-pop songs won |

**4. Doubling energy, halving genre**

Energy weight 1.5 → 3.0, genre 2.0 → 1.0. Happy Pop got better (Gym Hero dropped from #3 to #5). Sad Raver got worse (all sad songs disappeared and loud metal took their place). So the change made results different, not clearly more accurate. Details are in the [model card](model_card.md#7-evaluation).

**5. Adding advanced song features**

I added popularity, release decade, mood tags, instrumentalness and an explicit flag. For Happy Pop, the "no explicit songs" setting and the "uplifting/sunny" tags pushed Gym Hero from #3 down to #5, and Rooftop Lights moved up to #3. That fixed the result that felt most wrong before. Intense Rock picked up the metal song Iron Verdict through the shared "aggressive" tag.

See the full outputs in [Sample Recommendation Output](#sample-recommendation-output).

---

## Limitations and Risks

- **Tiny catalog:** only 23 songs. Most genres have just 1 song (rock has only one), so some users get poor matches.
- **Genre is too strong:** a genre match (+2.0) can beat what the user actually wants to feel right now.
- **Exact text matching:** "Pop" and "pop" are treated as different. Similar genres like "pop" and "indie pop" get no credit for each other.
- **No input checks:** values outside 0 to 1 are accepted and can give strange or negative scores.
- **Ignores lyrics, language, artist and listening history.** It only knows the numbers in the CSV.
- **Same-y results:** it can recommend several songs by the same artist or that sound alike.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Building this showed me that a recommender is really just a scoring rule. Each song gets points for matching what the user said they like, and the songs are sorted by points. The "smart" part comes from choosing which features to use and how much each one is worth. Small changes to those weights, like lowering genre from 2.0 to 0.5, can completely change what a user sees.

I also saw how bias can sneak in. Users whose favorite genre has many songs in the catalog (pop, lofi) get great matches, while a rock fan only has one good option. A typo or a capital letter can silently ruin someone's results. Real apps have the same problems at a bigger scale: if the data or the weights favor some kinds of music or users, other people get worse recommendations without knowing why.
