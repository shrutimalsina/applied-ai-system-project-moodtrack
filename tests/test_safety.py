import pytest

from src.safety import MAX_CHARS, check_distress, validate_entry


# ---------- Input validation ----------

@pytest.mark.parametrize("entry", [None, "", "   ", "\n\t"])
def test_empty_entry_is_rejected(entry):
    result = validate_entry(entry)
    assert not result.ok
    assert result.message


def test_too_short_entry_is_rejected():
    assert not validate_entry("sad").ok


def test_long_entry_is_trimmed_with_warning():
    result = validate_entry("today was fine " * 500)
    assert result.ok
    assert len(result.text) == MAX_CHARS
    assert result.warnings


def test_whitespace_is_cleaned():
    assert validate_entry("  i   feel\n\ngood today  ").text == "i feel good today"


# ---------- Distress detection ----------

@pytest.mark.parametrize("entry", [
    "I want to die",
    "honestly i dont want to be here anymore",
    "I can't do this anymore, everyone would be better off without me",
    "I keep thinking about hurting myself",
    "I've been having suicidal thoughts",
    "sometimes I think about ending my life",
    "There's no reason to live",
    "I CANT TAKE IT ANYMORE",
    "I’m going to kill myself",  # curly apostrophe
])
def test_distress_is_detected(entry):
    result = check_distress(entry)
    assert result.distress
    assert "988" in result.message


@pytest.mark.parametrize("entry", [
    "this exam is killing me lol",
    "I'm dying to see that concert",
    "I almost died laughing at my friend's joke",
    "I feel sad and tired after a long week",
    "My plant died and I'm a bit upset",
])
def test_everyday_language_is_not_flagged(entry):
    assert not check_distress(entry).distress


def test_journal_text_is_not_logged(caplog):
    secret = "I want to die because of my secret"
    with caplog.at_level("WARNING"):
        check_distress(secret)
    assert "want_to_die" in caplog.text
    assert "secret" not in caplog.text
