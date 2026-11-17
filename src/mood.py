"""Turn the emotion model's guesses into a spot on the mood grid.

The mood grid has two directions, the same two numbers every song has:
  - valence: how positive (0 = very negative, 1 = very positive)
  - energy:  how intense  (0 = very calm,     1 = very intense)

Each emotion has a home spot on the grid (sadness is negative and low-energy,
anger is negative and high-energy, and so on). We blend the spots of the two
most likely emotions to get the writer's current mood.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from src.prepare_data import label_mood

log = logging.getLogger("mood")

# Home spot of each emotion as (valence, energy)
EMOTION_POINTS: Dict[str, Tuple[float, float]] = {
    "joy":      (0.80, 0.65),
    "love":     (0.80, 0.45),
    "surprise": (0.65, 0.75),
    "anger":    (0.15, 0.85),
    "fear":     (0.20, 0.70),
    "sadness":  (0.15, 0.25),
    # The model can't detect "calm" (its training data had no calm label),
    # but users can pick it when they correct their mood.
    "calm":     (0.65, 0.25),
}

# Where each listening goal ends up on the grid. "stay" means stay where you are.
GOALS: Dict[str, Tuple[str, Optional[Tuple[float, float]]]] = {
    "calm":     ("Calm down",              (0.60, 0.25)),
    "lift":     ("Feel a bit better",      (0.70, 0.50)),
    "energize": ("Get energized",          (0.80, 0.85)),
    "stay":     ("Stay with this feeling", None),
}

# Below this confidence, the app asks the user to confirm their mood
CONFIDENCE_THRESHOLD = 0.50


@dataclass
class MoodReading:
    emotions: Dict[str, float]  # every emotion with its probability, highest first
    top_emotion: str
    confidence: float           # probability of the top emotion (0 to 1)
    valence: float
    energy: float
    mood: str                   # happy / peaceful / intense / melancholy
    needs_check: bool           # True if the model isn't sure enough


def blend_top_two(emotions: Dict[str, float]) -> Tuple[float, float]:
    """Weighted average of the two most likely emotions' home spots.

    Only blends when both emotions are on the same side (both positive or both
    negative). Averaging "happy" and "sad" would land on "neutral", which is
    neither, so in that case we use the top emotion alone.
    """
    items = list(emotions.items())
    first, p1 = items[0]
    v1, e1 = EMOTION_POINTS[first]
    if len(items) < 2:
        return v1, e1
    second, p2 = items[1]
    v2, e2 = EMOTION_POINTS[second]
    if (v1 >= 0.5) != (v2 >= 0.5):
        return v1, e1
    total = p1 + p2
    return round((v1 * p1 + v2 * p2) / total, 3), round((e1 * p1 + e2 * p2) / total, 3)


def read_mood(text: str, model) -> MoodReading:
    """Run the emotion model on a journal entry and place the result on the mood grid."""
    emotions = model.predict(text)
    top_emotion, confidence = next(iter(emotions.items()))
    valence, energy = blend_top_two(emotions)
    reading = MoodReading(
        emotions=emotions,
        top_emotion=top_emotion,
        confidence=confidence,
        valence=valence,
        energy=energy,
        mood=label_mood(valence, energy),
        needs_check=confidence < CONFIDENCE_THRESHOLD,
    )
    log.info("Mood: top=%s (%.2f) -> valence=%.2f energy=%.2f (%s), needs_check=%s",
             top_emotion, confidence, valence, energy, reading.mood, reading.needs_check)
    return reading


def correct_mood(emotion: str) -> MoodReading:
    """The user said how they actually feel, so trust them fully (confidence = 1)."""
    if emotion not in EMOTION_POINTS:
        raise ValueError(f"Unknown emotion '{emotion}'. Choose from: {', '.join(EMOTION_POINTS)}")
    valence, energy = EMOTION_POINTS[emotion]
    log.info("User corrected mood to %s", emotion)
    return MoodReading(
        emotions={emotion: 1.0}, top_emotion=emotion, confidence=1.0,
        valence=valence, energy=energy, mood=label_mood(valence, energy), needs_check=False,
    )


def goal_point(goal: str, reading: MoodReading) -> Tuple[float, float]:
    """Where on the grid the playlist should end up."""
    if goal not in GOALS:
        raise ValueError(f"Unknown goal '{goal}'. Choose from: {', '.join(GOALS)}")
    point = GOALS[goal][1]
    return point if point is not None else (reading.valence, reading.energy)


def suggest_goal(reading: MoodReading) -> str:
    """A sensible default goal; the user can always pick a different one."""
    return {
        "melancholy": "lift",     # low and sad: gently lift
        "intense": "calm",        # angry or anxious: calm down
        "peaceful": "stay",       # already calm and positive
        "happy": "stay",          # already feeling good
    }[reading.mood]
