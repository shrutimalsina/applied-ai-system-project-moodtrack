"""Emotion readers: read a journal entry and predict how the writer feels.

There are two readers:
  1. PretrainedEmotionModel (MAIN): a ready-made AI model that someone else
     trained on six kinds of real writing (Reddit, tweets, TV dialogue, and
     people describing events in their lives). Downloaded on first use.
  2. EmotionModel (BASELINE + BACKUP): the small model trained in this project.
     It scores 88% on its own test sentences but does much worse on everyday
     journal writing, because its training data is almost all tweets that start
     with "i feel...". It is kept for comparison, and as a backup if the main
     model can't be loaded.

Train the baseline model (from the project root):
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
import os
import threading
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
    """The baseline model trained in this project. Predicts 6 emotions with confidence scores."""

    name = "baseline (trained in this project)"

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


PRETRAINED_NAME = "j-hartmann/emotion-english-distilroberta-base"


class PretrainedEmotionModel:
    """Main reader: "Emotion English DistilRoBERTa-base" by Jochen Hartmann (2022).

    https://huggingface.co/j-hartmann/emotion-english-distilroberta-base
    Predicts 7 labels: anger, disgust, fear, joy, neutral, sadness, surprise.
    It's a transformer, the same basic technology as ChatGPT but much smaller,
    so it reads words in context instead of just counting them.
    """

    name = "pretrained (DistilRoBERTa emotion model)"

    def __init__(self, model_name: str = PRETRAINED_NAME):
        if self.is_downloaded(model_name):
            # Already on this computer: don't check the internet (faster, works offline)
            os.environ["HF_HUB_OFFLINE"] = "1"
        else:
            print("Downloading the emotion model for the first time (about 330 MB, only once)...")

        # PyTorch prints a harmless macOS-only warning when it loads; hide it
        logging.getLogger("torch.distributed.elastic.multiprocessing.redirects").setLevel(logging.ERROR)

        # Imported here so the rest of the app still works if these aren't installed
        from transformers import pipeline
        from transformers.utils import logging as hf_logging

        hf_logging.set_verbosity_error()      # hide download/progress messages
        hf_logging.disable_progress_bar()
        self.pipeline = pipeline("text-classification", model=model_name, top_k=None)

    @staticmethod
    def is_downloaded(model_name: str) -> bool:
        """True if the model files are already in the Hugging Face download folder."""
        hf_home = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface"))
        folder = hf_home / "hub" / ("models--" + model_name.replace("/", "--")) / "snapshots"
        return folder.exists() and any(folder.iterdir())

    def predict(self, text: str) -> Dict[str, float]:
        """Return {emotion: probability}, highest first. Probabilities add up to 1."""
        scores = self.pipeline(text[:2000], truncation=True)[0]
        ranked = sorted(scores, key=lambda s: s["score"], reverse=True)
        return {s["label"]: round(float(s["score"]), 3) for s in ranked}


_reader = None
_reader_lock = threading.Lock()  # the app may start loading in the background


def load_emotion_reader():
    """Load the main model once; if that fails, fall back to the baseline model."""
    global _reader
    with _reader_lock:
        if _reader is None:
            try:
                reader = PretrainedEmotionModel()
                reader.predict("warm up")  # the first prediction is slow, so do it now
            except Exception as error:  # not installed, no internet on first run, etc.
                log.warning("Pretrained model unavailable (%s); using baseline model instead", error)
                reader = EmotionModel()
            _reader = reader
            log.info("Emotion reader: %s", _reader.name)
    return _reader


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    train()
