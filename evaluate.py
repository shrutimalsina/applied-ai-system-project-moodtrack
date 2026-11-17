"""Run MoodTrack on fixed examples and write a Markdown report."""

import argparse
import csv
from pathlib import Path

from src.agent import MAX_ATTEMPTS, STEPS, build_playlist
from src.emotion_model import EmotionModel, PretrainedEmotionModel
from src.mood import EMOTION_POINTS, read_mood
from src.moodtrack import MoodTrack
from src.safety import validate_entry

CASES_PATH = Path("evaluation/journal_entries.csv")
REPORT_PATH = Path("evaluation/results.md")


class EvaluationApp(MoodTrack):
    def __init__(self, model):
        super().__init__()
        self.reader = model

    @property
    def model(self):
        return self.reader


def rate(count, total):
    return f"{count}/{total} ({count / total:.0%})" if total else "0/0 (no cases)"


def mood_matches(reading, expected):
    exact = reading.top_emotion in expected
    same_side = any(
        (reading.valence >= 0.5) == (EMOTION_POINTS[label][0] >= 0.5)
        for label in expected
    )
    return exact, same_side


def run(cases, baseline, pretrained):
    app = EvaluationApp(pretrained)
    checks = []
    mood_rows = []
    comparisons = []
    attempts = []
    playlist_checks = repeat_checks = flagged = unsure = errors = flagged_errors = 0

    for case in cases:
        case_id = case["id"]
        category = case["category"]
        entry = case["entry"]
        expected_status = case["expected_status"]
        result = app.check_entry(entry)
        passed = result.status == expected_status
        if expected_status != "ok":
            passed = passed and result.reading is None and bool(result.message)
        detail = f"Expected {expected_status}, got {result.status}"
        if expected_status == "ok" and result.status == "ok":
            reading = result.reading
            labels = case["expected_feelings"].split("|")
            before = read_mood(validate_entry(entry).text, baseline)
            before_scores = mood_matches(before, labels)
            after_scores = mood_matches(reading, labels)
            comparisons.append((before_scores, after_scores))
            flagged += reading.needs_check
            unsure += reading.unsure
            errors += not after_scores[0]
            flagged_errors += reading.needs_check and not after_scores[0]
            mood_rows.append(
                f"| {case_id} | {case['author']} | {', '.join(labels)} | "
                f"{before.top_emotion} | {reading.top_emotion} | "
                f"{'Yes' if reading.needs_check else 'No'} |"
            )
            if category == "negation":
                handled = after_scores[1] or reading.unsure
                passed = passed and handled
                detail += f". Negation handled: {'yes' if handled else 'no'}"
            if case["goal"]:
                goal = case["goal"]
                playlist = build_playlist(app.catalog, reading, goal, save_trace=False)
                again = app.check_entry(entry).reading
                repeated = build_playlist(app.catalog, again, goal, save_trace=False)
                critic_ok = (
                    playlist.passed and len(playlist.songs) == STEPS
                    and 1 <= playlist.attempts <= MAX_ATTEMPTS
                )
                repeat_ok = reading == again and playlist == repeated
                playlist_checks += critic_ok
                repeat_checks += repeat_ok
                attempts.append(playlist.attempts)
                passed = passed and critic_ok and repeat_ok
                detail += (
                    f". Critic: {'pass' if critic_ok else 'fail'} "
                    f"in {playlist.attempts} attempt(s). "
                    f"Repeat: {'same' if repeat_ok else 'different'}"
                )
                if playlist.problems:
                    detail += f". Problems: {', '.join(playlist.problems)}"
        checks.append((case_id, category, passed, detail))

    total = len(comparisons)
    report = [
        "# MoodTrack evaluation",
        "",
        f"Baseline: {baseline.name}. Pretrained: {pretrained.name}.",
        "",
        "Exact means the top feeling matches any listed answer. Right side means the "
        "prediction and at least one listed answer are on the same half of the mood "
        "grid. MoodTrack puts neutral and surprise on the positive half. These are "
        "small, hand-labeled examples. Accuracy is reported separately from PASS/FAIL.",
        "",
        "| Reader | Exact | Right side |",
        "| --- | --- | --- |",
    ]
    for index, name in enumerate(("Baseline", "Pretrained")):
        exact = sum(pair[index][0] for pair in comparisons)
        side = sum(pair[index][1] for pair in comparisons)
        report.append(f"| {name} | {rate(exact, total)} | {rate(side, total)} |")
    report.extend([
        "",
        "Interactive MoodTrack always asks the user to confirm or correct the mood. "
        "The flags below count entries it specifically marked for review.",
        "",
        f"- Flagged for review: {rate(flagged, total)}",
        f"- Required a mood choice: {rate(unsure, total)}",
        f"- Exact-label errors flagged: {rate(flagged_errors, errors)}",
        f"- Playlists that passed the critic: {rate(playlist_checks, len(attempts))}",
        f"- Repeat runs with identical mood and playlist results: "
        f"{rate(repeat_checks, len(attempts))}",
        f"- Attempts per playlist: {', '.join(map(str, attempts)) or 'none'}",
        "",
        "| Case | Author | Expected feelings | Baseline | Pretrained | Flagged |",
        "| --- | --- | --- | --- | --- | --- |",
        *mood_rows,
        "",
        "## Pass/fail checks",
        "",
        "| Case | Category | Result | Details |",
        "| --- | --- | --- | --- |",
    ])
    for case_id, category, passed, detail in checks:
        report.append(f"| {case_id} | {category} | {'PASS' if passed else 'FAIL'} | {detail} |")
    passed_count = sum(check[2] for check in checks)
    summary = f"{passed_count} PASS, {len(checks) - passed_count} FAIL"
    report.extend(["", f"**{summary}**"])
    return "\n".join(report) + "\n", summary, passed_count == len(checks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=REPORT_PATH)
    args = parser.parse_args()
    with CASES_PATH.open(encoding="utf-8", newline="") as source:
        cases = list(csv.DictReader(source))
    try:
        baseline = EmotionModel()
        pretrained = PretrainedEmotionModel()
    except Exception as error:
        parser.exit(2, f"Could not load both emotion models: {error}\n")
    report, summary, passed = run(cases, baseline, pretrained)
    args.output.write_text(report, encoding="utf-8")
    print(f"{summary}\nReport saved to {args.output}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
