"""MoodTrack: write how you feel, get a playlist that meets you there and moves you
toward how you want to feel.

Interactive (asks you questions):
    python -m src.moodtrack

One line (good for scripts and copying into docs):
    python -m src.moodtrack --entry "I feel so alone today" --goal lift
    python -m src.moodtrack --entry "..." --mood calm --goal stay --genre jazz

Everything the app does is logged to logs/moodtrack.log (without your journal text).
"""

import argparse
import logging
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.agent import PlaylistResult, build_playlist, describe_point
from src.catalog import Catalog
from src.emotion_model import load_emotion_reader
from src.mood import EMOTION_POINTS, GOALS, MoodReading, correct_mood, read_mood, suggest_goal
from src.safety import check_distress, validate_entry

LOG_FILE = Path("logs/moodtrack.log")
log = logging.getLogger("moodtrack")


def setup_logging() -> None:
    """Send detailed logs to a file so the screen stays clean."""
    LOG_FILE.parent.mkdir(exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE, level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)-12s %(message)s",
    )


@dataclass
class EntryCheck:
    status: str                       # "ok", "invalid" or "distress"
    message: str = ""
    reading: Optional[MoodReading] = None
    warnings: tuple = ()


class MoodTrack:
    """Holds the song catalog and the emotion model, and runs the two halves of a request."""

    def __init__(self):
        self.catalog = Catalog()
        self.genres = set(self.catalog.df["genre"])

    @property
    def model(self):
        # Loaded once and shared; may already be loading in the background
        return load_emotion_reader()

    def check_entry(self, entry: Optional[str]) -> EntryCheck:
        """Validate -> safety check -> read mood. Stops early if something is wrong."""
        validation = validate_entry(entry)
        if not validation.ok:
            return EntryCheck("invalid", validation.message)
        safety = check_distress(validation.text)
        if safety.distress:
            return EntryCheck("distress", safety.message)
        reading = read_mood(validation.text, self.model)
        return EntryCheck("ok", reading=reading, warnings=tuple(validation.warnings))

    def make_playlist(self, reading: MoodReading, goal: str, genre: str = "") -> PlaylistResult:
        return build_playlist(self.catalog, reading, goal, genre)


# ---------------------------------------------------------------- screen output

def show_reading(reading: MoodReading) -> None:
    emotions = list(reading.emotions.items())
    print("\nWhat I picked up from your entry:")
    if reading.unsure:
        # Don't present a shaky guess as if it were an answer
        print(f"  {reading.reason}")
        print("  My best guesses were: " + ", ".join(f"{e} ({p:.0%})" for e, p in emotions[:3]))
        return
    print(f"  Strongest feeling: {emotions[0][0]} ({emotions[0][1]:.0%} sure)")
    if len(emotions) > 1:
        print("  Also present:      " + ", ".join(f"{e} ({p:.0%})" for e, p in emotions[1:3]))
    print(f"  Mood: {reading.mood} ({describe_point(reading.valence, reading.energy)})")
    if reading.needs_check:
        print(f"  {reading.reason} Please check it.")


def show_playlist(result: PlaylistResult, reading: MoodReading, goal: str) -> None:
    print(f"\nYour playlist: {reading.top_emotion} -> {GOALS[goal][0].lower()}")
    print("-" * 60)
    for i, song in enumerate(result.songs, start=1):
        print(f"{i}. {song['title']} - {song['artist']}  [{song['genre']}]")
        print(f"   {song['why']}")
    print("-" * 60)
    if result.passed:
        print(f"Agent check: passed all rules (attempts: {result.attempts})")
    else:
        print(f"Agent check: best effort, still has problems: {', '.join(result.problems)}")
    if result.trace_file:
        print(f"Agent reasoning saved to {result.trace_file}")


# ---------------------------------------------------------------- questions (interactive mode)

def ask(prompt: str) -> str:
    return input(prompt).strip().lower()


def ask_mood(reading: MoodReading) -> MoodReading:
    choices = ", ".join(EMOTION_POINTS)
    while True:
        if reading.unsure:
            # No default here: the user has to say how they feel
            answer = ask(f"\nHow are you feeling? Type one of: {choices}: ")
        else:
            answer = ask(f"\nIs that right? Press Enter for yes, or type how you feel ({choices}): ")
            if answer in ("", "y", "yes"):
                return reading
        if answer in EMOTION_POINTS:
            return correct_mood(answer)
        print(f"  Sorry, I don't know '{answer}'. Try one of: {choices}")


def ask_goal(reading: MoodReading) -> str:
    keys = list(GOALS)
    suggested = suggest_goal(reading)
    print("\nWhere would you like the music to take you?")
    for i, key in enumerate(keys, start=1):
        print(f"  {i}. {GOALS[key][0]}" + ("   (suggested)" if key == suggested else ""))
    while True:
        answer = ask("Pick 1-4, or press Enter for the suggestion: ")
        if answer == "":
            return suggested
        if answer.isdigit() and 1 <= int(answer) <= len(keys):
            return keys[int(answer) - 1]
        print("  Please type a number from 1 to 4.")


def ask_genre(app: MoodTrack) -> str:
    while True:
        answer = ask("\nFavorite genre? (optional, e.g. pop, jazz, rock; Enter to skip): ")
        if answer == "" or answer in app.genres:
            return answer
        print(f"  '{answer}' isn't in the catalog. Some options: pop, rock, jazz, acoustic, hip-hop, classical")


# ---------------------------------------------------------------- main

def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="MoodTrack: journal entry in, mood-based playlist out.")
    parser.add_argument("--entry", help="your journal entry (skips the questions)")
    parser.add_argument("--mood", choices=list(EMOTION_POINTS), help="override the detected mood")
    parser.add_argument("--goal", choices=list(GOALS), help="where the playlist should take you")
    parser.add_argument("--genre", default="", help="optional favorite genre, e.g. jazz")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    setup_logging()
    interactive = args.entry is None

    try:
        app = MoodTrack()
    except FileNotFoundError as error:
        print(f"Setup problem: {error}")
        return 1

    print("MoodTrack - a playlist for how you feel")
    if interactive:
        # Load the AI model in the background while the user types (it takes a few seconds)
        threading.Thread(target=load_emotion_reader, daemon=True).start()
        entry = input("\nWrite a few sentences about how you're feeling today:\n> ")
    else:
        entry = args.entry
        print(f"\nJournal entry: \"{entry}\"")

    check = app.check_entry(entry)
    if check.status == "invalid":
        print(f"\n{check.message}")
        return 1
    if check.status == "distress":
        print(f"\n{check.message}")
        return 0
    for warning in check.warnings:
        print(f"Note: {warning}")

    reading = check.reading
    show_reading(reading)

    if args.mood:
        reading = correct_mood(args.mood)
        print(f"  Mood set by you: {args.mood}")
    elif interactive:
        reading = ask_mood(reading)
    elif reading.unsure:
        print("  Using my best guess. Add --mood to set it yourself.")

    goal = args.goal or (ask_goal(reading) if interactive else suggest_goal(reading))
    genre = args.genre.lower()
    if genre and genre not in app.genres:
        print(f"Note: genre '{genre}' isn't in the catalog, so I'll ignore it.")
        genre = ""
    elif interactive and not genre:
        genre = ask_genre(app)

    log.info("Request: goal=%s genre=%s mood=%s corrected=%s",
             goal, genre or "-", reading.top_emotion, reading is not check.reading)
    show_playlist(app.make_playlist(reading, goal, genre), reading, goal)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
        sys.exit(0)
