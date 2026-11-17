# MoodTrack

MoodTrack turns a short journal entry into a five-song playlist. Its goal is to start with music that fits how you feel and move gradually toward the mood you choose. It explains why each song was picked.

## Base project

**Music Recommender Simulation (Modules 1–3)** ranked 23 made-up songs based on a user's taste profile, including genre, mood, energy, how positive the song sounds, and how acoustic it is. It scored each song and showed the top five with reasons. MoodTrack uses that same scoring code to rank nearby songs from a catalog of 80,200 real tracks.

## How it works

1. The app checks the entry for missing text and crisis phrases.
2. A trained emotion model guesses the strongest feeling and places it on a grid from dark to bright and calm to intense.
3. In interactive mode, you confirm or correct the guess, choose a listening goal, and can pick a genre.
4. The playlist agent plans five points from your starting mood to your goal. At each point, it finds nearby tracks and ranks them using the original scorer.
5. A rule checker, called the critic, looks for problems such as repeated artists, songs too far from the plan, or explicit tracks when the starting mood is melancholy or intense. The agent tries up to three times and reports any remaining problems.

See the [Mermaid architecture source](diagrams/architecture.mmd) and [example agent traces](ai_interactions.md).

## Install and run

From the project folder, create a virtual environment to keep this project's Python packages together.

```bash
python3 -m venv .venv
```

Activate it on macOS or Linux.

```bash
source .venv/bin/activate
```

Install the packages.

```bash
python -m pip install -r requirements.txt
```

Start MoodTrack.

```bash
python -m src.moodtrack
```

The clean song catalog and baseline emotion model are included. The first run downloads the main emotion model (about 330 MB). Later runs can use the saved download. MoodTrack uses the included baseline if loading the main model fails.

## Sample runs

These are excerpts from runs with the pretrained model. Each run prints reasons for the song choices and saves a trace in `logs/traces/`.

```bash
python -m src.moodtrack --entry "I got the internship i worked so hard for!" --goal energize
```

```text
Strongest feeling: joy (80% sure)
Mood: happy (bright, energetic)

Your playlist: joy -> get energized
1. Mallipoo - A.R. Rahman, Madhushree  [pop-film]
2. Pied Piper - BTS  [k-pop]
3. Break on Through (To the Other Side) - The Doors  [psych-rock]
4. La Zona - Bad Bunny  [latino]
5. Losing My Religion - R.E.M.  [alt-rock]
Agent check: passed all rules (attempts: 1)
```

```bash
python -m src.moodtrack --entry "My best friend stopped talking to me and I feel so alone" --goal lift
```

```text
Strongest feeling: sadness (99% sure)
Mood: melancholy (very dark, calm)

Your playlist: sadness -> feel a bit better
1. Out Of Love - Alessia Cara  [electro]
2. Arcade - Duncan Laurence  [pop]
3. Falling for U - Peachy!, mxmtoon  [chill]
4. Free Fallin' - Tom Petty  [folk]
5. Sunday Best - Surfaces  [soul]
Agent check: passed all rules (attempts: 2)
```

## Guardrail examples

| Input | What MoodTrack does | Result |
| --- | --- | --- |
| `Really tired` | Checks for at least three words before running the emotion model. | Asks for more words and stops without a playlist. |
| `I want to die and I need help.` (test example) | Matches a crisis phrase before running the emotion model. | Shows a support message and stops without a playlist. |
| `i dont feel happy at all` | Flags the model's 99% joy guess because the text says “don't feel happy.” | Interactive mode asks the user to choose a mood. With `--entry`, the app warns and uses its guess unless the user supplies `--mood`. |
| `My best friend stopped talking to me and I feel so alone` with goal `lift` | The critic finds an explicit song at step 2 and the agent retries with explicit songs turned off. | Arcade replaces that song. The second playlist passes. |

## Test and evaluate

Run the unit tests.

```bash
python -m pytest
```

Run the end-to-end evaluation, which requires both emotion models.

```bash
python evaluate.py
```

```text
33 PASS, 0 FAIL
Report saved to evaluation/results.md
```

The evaluation checks input handling, crisis phrases, playlist rules, and repeat runs. On 22 labeled mood entries, the baseline matched 7 expected feelings and the pretrained model matched 13. See the [evaluation report](evaluation/results.md) and [model card](model_card.md) for what these results cover.
