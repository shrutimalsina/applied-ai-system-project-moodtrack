"""Guardrails that run BEFORE the AI sees a journal entry.

1. validate_entry: rejects empty / too-short input and trims very long input.
2. check_distress: looks for signs of self-harm or crisis. If found, MoodTrack
   shows support resources instead of a playlist. Music is not the right
   response to someone in crisis, and sad songs could make things worse.

Design choices:
- Uses a fixed list of phrases on purpose, not the AI model. The emotion model
  was never taught what a crisis looks like, and a safety check should behave
  the same way every time so it's easy to check.
- Plays it safe: a false alarm costs the user one extra screen, a missed
  crisis costs far more.
- Privacy: the journal text is never saved to the logs, only which phrase
  rule matched.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

MIN_WORDS = 3
MAX_CHARS = 2000

log = logging.getLogger("safety")


@dataclass
class ValidationResult:
    ok: bool
    text: str = ""
    message: str = ""
    warnings: List[str] = field(default_factory=list)


def validate_entry(raw: Optional[str]) -> ValidationResult:
    """Clean the entry and decide whether there is enough to work with."""
    if raw is None or not raw.strip():
        log.info("Validation failed: empty entry")
        return ValidationResult(False, message="Please write a few words about how you're feeling.")

    # Remove control characters and collapse whitespace
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", " ", raw)
    text = re.sub(r"\s+", " ", text).strip()

    if len(re.findall(r"[A-Za-z']+", text)) < MIN_WORDS:
        log.info("Validation failed: too short")
        return ValidationResult(False, message=f"Please write at least {MIN_WORDS} words so I can understand your mood.")

    warnings = []
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]
        warnings.append(f"Your entry was long, so only the first {MAX_CHARS} characters were used.")
        log.info("Entry trimmed to %d characters", MAX_CHARS)

    return ValidationResult(True, text=text, warnings=warnings)


# Each rule is (name, pattern). Patterns run on lowercased text with apostrophes removed,
# so "can't" and "cant" both match.
DISTRESS_RULES = [
    ("suicide", r"\bsuicid(e|al)\b|\bkill(ing)? myself\b|\bend(ing)? (my|it all|my own) li(fe|ves)\b|\bend it all\b|\bunalive\b"),
    ("want_to_die", r"\b(want|wanna|wish|ready|going) to die\b|\bwish i (was|were) dead\b|\bbetter off dead\b"),
    ("self_harm", r"\b(hurt|harm|cut|cutting|hurting|harming) myself\b|\bself[- ]?harm\b"),
    ("no_reason_to_live", r"\bno (reason|point) (to|in) (live|living|going on)\b|\bdont want to (live|be alive|be here anymore|exist)\b"),
    ("burden", r"\b(better off|happier) without me\b|\beveryone would be better\b"),
    ("cant_go_on", r"\bcant (go on|do this anymore|take it anymore)\b"),
    ("overdose", r"\boverdos(e|ing)\b|\btake all (my|the) pills\b"),
]

SUPPORT_MESSAGE = """It sounds like you're going through something really heavy right now.
You don't have to deal with it alone, and talking to someone can help.

  - Call or text 988 (Suicide & Crisis Lifeline, US, 24/7)
  - Text HOME to 741741 (Crisis Text Line, US)
  - Outside the US: findahelpline.com lists free local services
  - If you are in immediate danger, call your local emergency number

MoodTrack is a music app, not a substitute for support from a real person.
When you're ready, you can come back and write a new entry."""


@dataclass
class SafetyResult:
    distress: bool
    matched_rules: List[str] = field(default_factory=list)
    message: str = ""


def _normalize(text: str) -> str:
    text = text.lower().replace("’", "'").replace("'", "")
    return re.sub(r"\s+", " ", text)


def check_distress(text: str) -> SafetyResult:
    """Return distress=True with a support message if any crisis rule matches."""
    normalized = _normalize(text)
    matched = [name for name, pattern in DISTRESS_RULES if re.search(pattern, normalized)]
    if matched:
        # Log WHICH rules fired, never the journal text
        log.warning("Safety check triggered: %s", ", ".join(matched))
        return SafetyResult(True, matched, SUPPORT_MESSAGE)
    return SafetyResult(False)
