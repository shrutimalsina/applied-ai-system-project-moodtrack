"""Song catalog + retriever.

The cleaned Kaggle catalog has 80,000+ songs, too many to score one by one on
every request. The retriever narrows it down to a few hundred songs close to a
target point on the valence/energy mood map, then the ORIGINAL Module 1-3
scorer (recommender.recommend_songs) ranks those candidates.

    catalog (80k) --retrieve--> candidates (~300) --score_song--> top songs
"""

import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

from src.prepare_data import label_mood  # same mood labels the catalog uses
from src.recommender import recommend_songs

CATALOG_PATH = Path("data/tracks_clean.csv")

log = logging.getLogger("catalog")


class Catalog:
    def __init__(self, path: Path = CATALOG_PATH):
        if not path.exists():
            raise FileNotFoundError(
                f"No catalog at {path}. Build it first with: python -m src.prepare_data"
            )
        self.df = pd.read_csv(path, keep_default_na=False)
        self.df["explicit"] = self.df["explicit"].astype(str).str.lower() == "true"
        log.info("Loaded %d songs from %s", len(self.df), path)

    def __len__(self) -> int:
        return len(self.df)

    def retrieve(
        self,
        valence: float,
        energy: float,
        radius: float = 0.08,
        limit: int = 300,
        exclude_ids: Iterable[int] = (),
        exclude_artists: Iterable[str] = (),
        allow_explicit: bool = True,
        min_popularity: int = 20,
    ) -> List[Dict]:
        """Return up to `limit` songs within `radius` of (valence, energy), closest first.

        If too few songs are found, the radius is widened step by step (and logged),
        so a request never comes back empty just because a mood region is sparse.
        """
        mask = ~self.df["id"].isin(list(exclude_ids)) & ~self.df["artist"].isin(list(exclude_artists))
        mask &= self.df["popularity"] >= min_popularity
        if not allow_explicit:
            mask &= ~self.df["explicit"]
        pool = self.df[mask]

        distance = np.hypot(pool["valence"] - valence, pool["energy"] - energy)
        while True:
            hits = pool[distance <= radius]
            if len(hits) >= 20 or radius >= 1.5:
                break
            log.info("Only %d songs within %.2f of (v=%.2f, e=%.2f); widening search",
                     len(hits), radius, valence, energy)
            radius *= 1.5

        hits = hits.assign(_dist=distance[hits.index]).sort_values("_dist").head(limit)
        return hits.drop(columns="_dist").to_dict("records")

    def recommend(self, valence: float, energy: float, k: int = 1,
                  favorite_genre: str = "", likes_acoustic: Optional[bool] = None,
                  **retrieve_kwargs) -> List[Dict]:
        """Retrieve candidates near the target mood, then rank them with the original scorer.

        Returns dicts with the song plus its score and the scorer's reasons.
        """
        candidates = self.retrieve(valence, energy, **retrieve_kwargs)
        if not candidates:
            return []

        user_prefs = {
            "favorite_genre": favorite_genre,
            "favorite_mood": label_mood(valence, energy),
            "target_energy": energy,
            "target_valence": valence,
            # Calm targets lean acoustic unless the user said otherwise
            "likes_acoustic": energy < 0.4 if likes_acoustic is None else likes_acoustic,
            "allow_explicit": retrieve_kwargs.get("allow_explicit", True),
        }
        ranked = recommend_songs(user_prefs, candidates, k=k)
        return [{**song, "score": score, "reasons": reasons} for song, score, reasons in ranked]
