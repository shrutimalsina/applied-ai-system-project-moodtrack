"""End-to-end tests: run the real app (real model, real catalog) like a user would."""

import pytest

import src.agent as agent
import src.moodtrack as moodtrack


@pytest.fixture(autouse=True)
def temp_logs(tmp_path, monkeypatch):
    # Keep test runs from filling the real logs/ folder
    monkeypatch.setattr(moodtrack, "LOG_FILE", tmp_path / "moodtrack.log")
    monkeypatch.setattr(agent, "TRACE_DIR", tmp_path / "traces")


def run(capsys, *args):
    code = moodtrack.main(list(args))
    return code, capsys.readouterr().out


def test_full_run_prints_five_songs_with_reasons(capsys):
    code, out = run(capsys, "--entry", "My best friend stopped talking to me and I feel so alone", "--goal", "lift")
    assert code == 0
    assert "Strongest feeling: sadness" in out
    for n in range(1, 6):
        assert f"\n{n}. " in out
    assert "Starts where you are" in out
    assert "Agent check: passed" in out


def test_same_input_gives_same_playlist(capsys):
    args = ("--entry", "i feel nervous about my presentation tomorrow", "--goal", "calm")
    _, first = run(capsys, *args)
    _, second = run(capsys, *args)
    strip = lambda text: [line for line in text.splitlines() if "saved to" not in line]
    assert strip(first) == strip(second)


def test_distress_shows_resources_and_no_playlist(capsys):
    code, out = run(capsys, "--entry", "I want to die, nothing matters anymore")
    assert code == 0
    assert "988" in out
    assert "playlist:" not in out


def test_too_short_entry_is_rejected(capsys):
    code, out = run(capsys, "--entry", "sad")
    assert code == 1
    assert "at least 3 words" in out


def test_user_mood_override_is_used(capsys):
    _, out = run(capsys, "--entry", "exams tomorrow and I am so stressed I cannot sleep",
                 "--mood", "fear", "--goal", "calm")
    assert "Mood set by you: fear" in out
    assert "fear -> calm down" in out


def test_unknown_genre_is_ignored_with_a_note(capsys):
    code, out = run(capsys, "--entry", "great day at the beach with friends", "--genre", "notagenre")
    assert code == 0
    assert "isn't in the catalog" in out
