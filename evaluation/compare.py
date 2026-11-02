"""Load the question set and decide whether a predicted result matches the gold result."""

from __future__ import annotations

import itertools
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from app.config import PROJECT_ROOT

QUESTIONS_PATH = PROJECT_ROOT / "evaluation" / "questions.json"
_NUMERIC_TEXT = re.compile(r"-?\d+(\.\d+)?")
_MAX_COLUMNS_TO_SEARCH = 12


@dataclass(frozen=True)
class Question:
    id: str
    category: str
    en: str
    ar: str
    gold: tuple[str, ...]  # Any of these queries gives an accepted answer. Empty = unanswerable.
    ordered: bool = False  # True when the order of the rows matters (e.g. a top-5 list).

    @property
    def answerable(self) -> bool:
        return bool(self.gold)

    def text(self, lang: str) -> str:
        return self.en if lang == "en" else self.ar


def load_questions(path: Path = QUESTIONS_PATH) -> list[Question]:
    items = json.loads(path.read_text(encoding="utf-8"))
    return [
        Question(
            id=item["id"],
            category=item["category"],
            en=item["en"],
            ar=item["ar"],
            gold=tuple(item["gold"]),
            ordered=item.get("ordered", False),
        )
        for item in items
    ]


def normalize(value: object) -> object:
    """Make equal answers compare equal: 2 == 2.0 == "02", numbers rounded to 2 decimals."""
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if _NUMERIC_TEXT.fullmatch(text):
            return round(float(text), 2)
        return text
    if isinstance(value, int | float):
        return round(float(value), 2)
    return value


def results_match(gold: list[list], predicted: list[list], ordered: bool = False) -> bool:
    """True if the predicted rows contain the gold answer.

    - Same number of rows; rows compared as a multiset, or in order when `ordered`.
    - Extra predicted columns are allowed (e.g. the model returns the country AND its
      total when only the country was asked), and column order does not matter.
    """
    if len(gold) != len(predicted):
        return False
    if not gold:
        return True
    gold_width, predicted_width = len(gold[0]), len(predicted[0])
    if predicted_width < gold_width:
        return False

    expected = [tuple(normalize(v) for v in row) for row in gold]
    expected_counts = Counter(expected)
    if predicted_width > _MAX_COLUMNS_TO_SEARCH:
        candidates = [tuple(range(gold_width))]
    else:
        candidates = itertools.permutations(range(predicted_width), gold_width)

    for columns in candidates:
        projected = [tuple(normalize(row[c]) for c in columns) for row in predicted]
        if ordered and projected == expected:
            return True
        if not ordered and Counter(projected) == expected_counts:
            return True
    return False
