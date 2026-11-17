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
    assert read_mood("exams tomorrow tonight", model).needs_check


def test_blend_is_between_two_emotions_on_the_same_side():
    valence, energy = blend_top_two({"anger": 0.5, "sadness": 0.5})
    assert EMOTION_POINTS["sadness"][1] < energy < EMOTION_POINTS["anger"][1]


def test_opposite_emotions_are_not_averaged_into_neutral():
    # "great day at the beach": joy 29%, sadness 27% should stay on the happy side
    assert blend_top_two({"joy": 0.29, "sadness": 0.27, "anger": 0.19}) == EMOTION_POINTS["joy"]


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


# ---------- "Not" guard and "couldn't tell" ----------

@pytest.mark.parametrize("entry", [
    "i dont feel happy at all",
    "I am not okay",
    "honestly I'm not doing well",
    "I don’t feel good today",
    "i cant feel happy anymore",
])
def test_negated_positive_is_not_trusted(entry):
    # The model says joy 99%, but the entry says "not happy" -> don't trust it
    reading = read_mood(entry, FakeModel({"joy": 0.99, "sadness": 0.01}))
    assert reading.unsure
    assert "not okay" in reading.reason


def test_negation_guard_ignores_negative_predictions():
    # If the model already says sadness, "not okay" agrees with it: nothing to flag
    reading = read_mood("I am not okay", FakeModel({"sadness": 0.88, "fear": 0.12}))
    assert not reading.needs_check


def test_happy_entry_without_negation_is_trusted():
    reading = read_mood("I can't stop smiling today", FakeModel({"joy": 0.97, "surprise": 0.03}))
    assert not reading.needs_check


def test_near_tie_means_model_cannot_tell():
    reading = read_mood("my sister is fighting with me",
                        FakeModel({"love": 0.24, "joy": 0.23, "anger": 0.22, "sadness": 0.21, "fear": 0.1}))
    assert reading.unsure
    assert "couldn't tell" in reading.reason


def test_neutral_and_disgust_have_grid_spots():
    assert read_mood("just a normal day today", FakeModel({"neutral": 0.9, "joy": 0.1})).mood == "peaceful"
    assert read_mood("that was so gross honestly", FakeModel({"disgust": 0.9, "anger": 0.1})).mood == "intense"
