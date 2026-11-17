"""Emotion classifier: reads a journal entry and predicts how the writer feels.

Train it (from the project root):
    python -m src.emotion_model

Data: "Emotions dataset for NLP" (Kaggle, praveengovi, CC BY-SA 4.0), built from
Saravia et al. 2018, "CARER: Contextualized Affect Representations for Emotion
Recognition". 20,000 English sentences, each labeled with one of six emotions.

How it works, in two steps:
  1. TF-IDF turns each sentence into numbers by counting its words, giving more
     weight to telling words ("hopeless") than common ones ("the").
  2. Logistic regression learns which words go with which emotion.
It trains in seconds, gives the same answer every time, and returns a
percentage for every emotion, which we use as the model's confidence.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.pipeline import Pipeline

DATA_DIR = Path("data/raw/emotions")
MODEL_PATH = Path("models/emotion_model.joblib")
METRICS_PATH = Path("models/emotion_model_metrics.json")
EMOTIONS = ["anger", "fear", "joy", "love", "sadness", "surprise"]

log = logging.getLogger("emotion_model")


def load_split(name: str) -> Tuple[List[str], List[str]]:
    """Read one split file. Each line looks like: 'i feel so alone today;sadness'."""
    texts, labels = [], []
    with open(DATA_DIR / f"{name}.txt", encoding="utf-8") as f:
        for line in f:
            text, label = line.strip().rsplit(";", 1)
            texts.append(text)
            labels.append(label)
    return texts, labels


def build_pipeline(c: float) -> Pipeline:
    return Pipeline([
        # Words and two-word phrases ("not happy" means something different from "happy")
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
        # class_weight="balanced" stops the model ignoring rare emotions like surprise
        ("clf", LogisticRegression(C=c, class_weight="balanced", max_iter=2000)),
    ])


def train() -> Dict:
    """Train on the train set, pick the best setting using the validation set,
    then check the final model ONCE on the test set it has never seen."""
    x_train, y_train = load_split("train")
    x_val, y_val = load_split("val")
    x_test, y_test = load_split("test")
    log.info("Loaded %d train / %d validation / %d test sentences", len(x_train), len(x_val), len(x_test))

    # C controls how closely the model fits the training data (too close = memorizing).
    # Try a few values and keep the one that does best on the validation set.
    # "F1" is a score from 0 to 1 that balances right guesses and missed ones, averaged over all 6 emotions.
    best_c, best_f1, best_model = None, -1.0, None
    for c in [1.0, 3.0, 10.0, 30.0]:
        model = build_pipeline(c).fit(x_train, y_train)
        val_f1 = f1_score(y_val, model.predict(x_val), average="macro")
        log.info("  C=%-5s validation macro-F1 = %.3f", c, val_f1)
        if val_f1 > best_f1:
            best_c, best_f1, best_model = c, val_f1, model

    # The test set is only used once, at the end
    test_pred = best_model.predict(x_test)
    metrics = {
        "chosen_C": best_c,
        "validation_macro_f1": round(best_f1, 3),
        "test_accuracy": round(accuracy_score(y_test, test_pred), 3),
        "test_macro_f1": round(f1_score(y_test, test_pred, average="macro"), 3),
        "per_emotion": classification_report(y_test, test_pred, output_dict=True, zero_division=0),
    }
    log.info("\nChosen C=%s", best_c)
    log.info("Test accuracy: %.1f%%   Test macro-F1: %.3f", 100 * metrics["test_accuracy"], metrics["test_macro_f1"])
    log.info("\n%s", classification_report(y_test, test_pred, digits=3, zero_division=0))

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(best_model, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))
    log.info("Saved model to %s and metrics to %s", MODEL_PATH, METRICS_PATH)
    return metrics


class EmotionModel:
    """Loads the trained model and predicts emotions with confidence scores."""

    def __init__(self, path: Path = MODEL_PATH):
        if not path.exists():
            raise FileNotFoundError(
                f"No trained model at {path}. Train it first with: python -m src.emotion_model"
            )
        self.pipeline = joblib.load(path)

    def predict(self, text: str) -> Dict[str, float]:
        """Return {emotion: probability}, highest first. Probabilities add up to 1."""
        probs = self.pipeline.predict_proba([text.lower()])[0]
        ranked = sorted(zip(self.pipeline.classes_, probs), key=lambda p: p[1], reverse=True)
        return {str(emotion): round(float(p), 3) for emotion, p in ranked}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    train()
