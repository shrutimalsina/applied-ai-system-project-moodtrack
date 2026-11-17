"""The MoodTrack agent: plans a playlist, checks its own work, and fixes problems.

The idea comes from music therapy (the "iso principle"): first play music that
MATCHES how someone feels, then change it a little at a time toward how they
want to feel. Jumping straight to happy songs when someone is sad usually
doesn't work.

The agent works in a loop:
  1. PLAN    draw a path of steps on the mood grid, from the current mood to the goal
  2. ACT     for each step, fetch the best song (retriever + original scorer)
  3. CHECK   a critic tests the playlist against a list of rules
  4. FIX     if a rule fails, change the plan to fix that problem and try again
  5. EXPLAIN describe in plain words why each song is there
Every step is written to a trace so you can see how it reached its answer.
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.catalog import Catalog
from src.mood import GOALS, MoodReading

log = logging.getLogger("agent")

STEPS = 5
MAX_ATTEMPTS = 3
MAX_GAP = 0.15          # a song may be at most this far from its step on the mood grid
BACKWARD_SLACK = 0.03   # small wobbles are OK; bigger steps away from the goal are not
TRACE_DIR = Path("logs/traces")


Point = Tuple[float, float]  # (valence, energy)


@dataclass
class Settings:
    """Knobs the agent can turn when it fixes a failed plan."""
    allow_explicit: bool = True
    min_popularity: int = 20
    radius: float = 0.08
    banned_ids: List[int] = field(default_factory=list)


@dataclass
class PlaylistResult:
    songs: List[Dict]
    path: List[Point]
    passed: bool
    problems: List[str]
    attempts: int
    trace: List[str]
    trace_file: Optional[Path] = None


def distance(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


# ---------------------------------------------------------------- 1. PLAN

def plan_path(start: Point, goal: Point, steps: int = STEPS) -> List[Point]:
    """Evenly spaced points from start to goal. Step 1 matches the current mood."""
    return [
        (round(start[0] + (goal[0] - start[0]) * i / (steps - 1), 3),
         round(start[1] + (goal[1] - start[1]) * i / (steps - 1), 3))
        for i in range(steps)
    ]


# ---------------------------------------------------------------- 2. ACT

def pick_songs(catalog: Catalog, path: List[Point], settings: Settings, genre: str = "") -> List[Optional[Dict]]:
    """One song per step. Never repeats a song or an artist."""
    songs, used_ids, used_artists = [], list(settings.banned_ids), []
    for valence, energy in path:
        found = catalog.recommend(
            valence, energy, k=1, favorite_genre=genre,
            radius=settings.radius, allow_explicit=settings.allow_explicit,
            min_popularity=settings.min_popularity,
            exclude_ids=used_ids, exclude_artists=used_artists,
        )
        song = found[0] if found else None
        songs.append(song)
        if song:
            used_ids.append(song["id"])
            used_artists.append(song["artist"])
    return songs


# ---------------------------------------------------------------- 3. CHECK

def critic(songs: List[Optional[Dict]], path: List[Point], goal: Point,
           reading: MoodReading, moving: bool, catalog: Catalog) -> List[Tuple[str, int]]:
    """Return a list of (problem, step index). An empty list means the playlist passed."""
    problems = []
    fragile = reading.mood in ("melancholy", "intense")

    for i, (song, target) in enumerate(zip(songs, path)):
        if song is None:
            problems.append(("no_song", i))
            continue
        # Every song must really exist in the catalog (no made-up songs)
        if not (catalog.df["id"] == song["id"]).any():
            problems.append(("not_in_catalog", i))
        if distance((song["valence"], song["energy"]), target) > MAX_GAP:
            problems.append(("too_far_from_step", i))
        if fragile and song["explicit"]:
            problems.append(("explicit_when_fragile", i))

    artists = [s["artist"] for s in songs if s]
    if len(artists) != len(set(artists)):
        problems.append(("repeated_artist", -1))

    # The playlist must keep heading toward the goal
    if moving and all(songs):
        gaps = [distance((s["valence"], s["energy"]), goal) for s in songs]
        for i in range(1, len(gaps)):
            if gaps[i] > gaps[i - 1] + BACKWARD_SLACK:
                problems.append(("moves_away_from_goal", i))
        if gaps[-1] >= gaps[0] and distance(path[0], goal) > MAX_GAP:
            problems.append(("does_not_reach_goal", -1))
    return problems


# ---------------------------------------------------------------- 4. FIX

def fix(problems: List[Tuple[str, int]], songs: List[Optional[Dict]], settings: Settings) -> List[str]:
    """Change the settings to fix each kind of problem. Returns what it changed."""
    changes = []
    kinds = {kind for kind, _ in problems}
    if "explicit_when_fragile" in kinds and settings.allow_explicit:
        settings.allow_explicit = False
        changes.append("turned off explicit songs (user is feeling low)")
    if kinds & {"no_song", "too_far_from_step"}:
        settings.min_popularity = max(0, settings.min_popularity - 10)
        settings.radius = round(settings.radius * 1.5, 3)
        changes.append(f"searched more songs (min popularity {settings.min_popularity}, radius {settings.radius})")
    for kind, i in problems:
        if kind == "moves_away_from_goal" and songs[i]:
            settings.banned_ids.append(songs[i]["id"])
            changes.append(f"replaced step {i + 1} ('{songs[i]['title']}') because it moved away from the goal")
    return changes


# ---------------------------------------------------------------- 5. EXPLAIN

def describe_point(valence: float, energy: float) -> str:
    """Plain-word description of a spot on the mood grid."""
    feel = ("very sad" if valence < 0.2 else "low" if valence < 0.4 else
            "neutral" if valence < 0.6 else "upbeat" if valence < 0.8 else "very happy")
    pace = ("very calm" if energy < 0.2 else "calm" if energy < 0.4 else
            "medium-energy" if energy < 0.6 else "energetic" if energy < 0.8 else "very intense")
    return f"{feel}, {pace}"


def explain(song: Dict, step: int, total: int, goal_name: str, moving: bool) -> str:
    sound = describe_point(song["valence"], song["energy"])
    extra = []
    if song["acousticness"] >= 0.6:
        extra.append("mostly acoustic")
    if song["instrumentalness"] >= 0.5:
        extra.append("few or no vocals")
    details = f" ({', '.join(extra)})" if extra else ""

    if not moving:
        role = "Fits how you feel right now"
    elif step == 0:
        role = "Starts where you are, so the music feels familiar"
    elif step == total - 1:
        role = f"Lands at your goal: {goal_name.lower()}"
    else:
        role = f"Moves you a step closer to '{goal_name.lower()}'"
    return f"{role}. Sounds {sound}{details}."


# ---------------------------------------------------------------- the loop

def build_playlist(catalog: Catalog, reading: MoodReading, goal: str,
                   genre: str = "", save_trace: bool = True) -> PlaylistResult:
    goal_name, goal_spot = GOALS[goal]
    start = (reading.valence, reading.energy)
    end = goal_spot if goal_spot is not None else start
    moving = goal_spot is not None and distance(start, end) > 0.05

    trace = [
        f"INPUT  mood={reading.top_emotion} ({reading.confidence:.0%}), "
        f"spot=(valence {start[0]:.2f}, energy {start[1]:.2f}), goal='{goal_name}'"
        + (f", genre='{genre}'" if genre else "")
    ]
    path = plan_path(start, end)
    trace.append("PLAN   " + " -> ".join(f"({v:.2f}, {e:.2f})" for v, e in path))

    settings = Settings()
    songs, problems = [], []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        songs = pick_songs(catalog, path, settings, genre)
        trace.append(f"ACT    attempt {attempt}: " + " | ".join(
            f"{s['title']} ({s['valence']:.2f}, {s['energy']:.2f})" if s else "NONE" for s in songs))

        problems = critic(songs, path, end, reading, moving, catalog)
        if not problems:
            trace.append(f"CHECK  attempt {attempt}: all rules passed")
            break
        trace.append(f"CHECK  attempt {attempt}: " + ", ".join(
            f"{kind}" + (f" (step {i + 1})" if i >= 0 else "") for kind, i in problems))

        if attempt < MAX_ATTEMPTS:
            changes = fix(problems, songs, settings)
            trace.append("FIX    " + ("; ".join(changes) if changes else "no fix available"))
            if not changes:
                break

    passed = not problems
    final = [s for s in songs if s]
    for i, song in enumerate(final):
        song["why"] = explain(song, i, len(final), goal_name, moving)
    trace.append(("RESULT passed" if passed else "RESULT returned best effort with problems: "
                  + ", ".join(k for k, _ in problems)) + f" after {attempt} attempt(s)")

    for line in trace:
        log.info(line)
    result = PlaylistResult(final, path, passed, [k for k, _ in problems], attempt, trace)
    if save_trace:
        result.trace_file = write_trace(trace)
    return result


def write_trace(trace: List[str]) -> Path:
    """Save the agent's reasoning to a markdown file (journal text is never included)."""
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    path = TRACE_DIR / f"trace_{datetime.now():%Y%m%d_%H%M%S_%f}.md"
    path.write_text("# MoodTrack agent trace\n\n```text\n" + "\n".join(trace) + "\n```\n")
    return path
