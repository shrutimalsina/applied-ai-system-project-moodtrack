# AI Interactions Log

## MoodTrack playlist agent

I used AI to design a five-step playlist and a critic that checks each result. The agent plans a path through the mood grid, ranks nearby tracks, checks the playlist, and changes its settings if a check fails. The traces show the steps the program took. They contain mood labels, track choices, and rule results.

- **Sadness → feel a bit better.** The first attempt picked an explicit track at step 2. The critic flagged it, the agent turned off explicit tracks, and the second attempt passed with Arcade at step 2. [Two-attempt trace](examples/traces/sadness-lift.md)
- **Joy → get energized.** The first playlist passed all critic checks, so the agent returned it after one attempt. [First-attempt trace](examples/traces/joy-energize.md)

## Earlier Music Recommender Simulation work

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I used Claude Code (in VS Code) to do Challenge 1 (advanced song features) and Challenge 4 (summary table). The goal was to add 5 new song attributes, make the scoring use them, and show the results in a readable table that includes the reasons for each score.

**Prompts used:**

- "Introduce 5 or more complex attributes to your dataset that are not currently present in the baseline data, such as Song Popularity (0-100), Release Decade, or Detailed Mood Tags. Update both data/songs.csv and the scoring logic in src/recommender.py so scoring accounts for the new attributes."
- "Improve the readability of your terminal output by providing a formatted table or summary... Ensure the table includes the 'reasons' for each score."
- When asked which challenges to do, I picked "1: New song features" and "4: Summary table".

**What did the agent generate or change?**

- `data/songs.csv`: added 5 columns for all 23 songs: `popularity`, `release_decade`, `mood_tags` (e.g. `cozy;rainy`), `instrumentalness` and `explicit`.
- `src/recommender.py`:
  - added the new fields to `Song` and `UserProfile`, with defaults so the old tests still work
  - made `load_songs` convert the new columns
  - added scoring rules: up to +0.5 popularity, +0.5 decade, +1.0 mood tags, +0.5 instrumental, and -1.0 for explicit songs when not allowed
  - new preferences are optional, so profiles without them score the same as before
- `src/main.py`:
  - added advanced preferences to the 3 normal profiles
  - added `max_score()` so each profile shows the right maximum (6.5 or 9.0)
  - added `print_table()`, a plain ASCII table with one reason per line, with no new library needed
- `README.md` and `model_card.md`: documented the new features and re-pasted the output.

**What did you verify or fix manually?**

- Checked one score by hand: Sunrise City for Happy Pop = 6.42 (core) + 0.50 popularity + 0.5 decade + 1.0 tags + 0.425 instrumental = 8.845, shown as 8.85. ✅
- Checked that the 5 edge-case profiles (which set no advanced preferences) give exactly the same songs and scores as before. ✅
- Ran `pytest`: 2 passed. ✅
- Checked that the results make sense: Gym Hero (explicit, "intense") dropped from #3 to #5 for Happy Pop, which matches my earlier feeling that it did not belong at #3.
- The new values in `songs.csv` were made up by the AI, since the songs are fictional. I reviewed them to make sure they fit each song (e.g. metal songs are "aggressive", lofi songs are "cozy" and instrumental).

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

<!-- e.g., Strategy, Factory, Observer, etc. -->

**How did AI help you brainstorm or implement it?**

<!-- Describe the conversation or suggestions that led to your decision -->

**How does the pattern appear in your final code?**

<!-- Point to the relevant class or method -->
