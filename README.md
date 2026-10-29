# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

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

Paste a sample of your recommender's output here as a text block so a reader can see what it produces:

```
# e.g.:
# User profile: genre=indie, mood=chill, energy=low
# Recommendations:
#   1. ...
#   2. ...
#   3. ...
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



