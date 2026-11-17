import pytest

from src.mood import (EMOTION_POINTS, blend_top_two, correct_mood, goal_point,
                      read_mood, suggest_goal)


class FakeModel:
    """Stands in for the real emotion model so tests control its answers."""

    def __init__(self, emotions):
        self.emotions = emotions

    def predict(self, text):
        return self.emotions


def test_confident_sadness_lands_in_melancholy():
    model = FakeModel({"sadness": 0.9, "fear": 0.05, "joy": 0.05})
    reading = read_mood("i feel so down", model)
    assert reading.mood == "melancholy"
    assert not reading.needs_check
    assert suggest_goal(reading) == "lift"


def test_unsure_model_asks_user_to_check():
    model = FakeModel({"anger": 0.4, "sadness": 0.35, "joy": 0.25})
    assert read_mood("exams tomorrow", model).needs_check


def test_blend_is_between_the_two_emotions():
    valence, energy = blend_top_two({"joy": 0.5, "sadness": 0.5})
    assert EMOTION_POINTS["sadness"][0] < valence < EMOTION_POINTS["joy"][0]
    assert EMOTION_POINTS["sadness"][1] < energy < EMOTION_POINTS["joy"][1]


def test_user_correction_is_trusted():
    reading = correct_mood("calm")
    assert reading.confidence == 1.0
    assert reading.mood == "peaceful"


def test_stay_goal_keeps_current_mood():
    reading = correct_mood("sadness")
    assert goal_point("stay", reading) == (reading.valence, reading.energy)


@pytest.mark.parametrize("bad", ["happyish", ""])
def test_unknown_emotion_is_rejected(bad):
    with pytest.raises(ValueError):
        correct_mood(bad)
