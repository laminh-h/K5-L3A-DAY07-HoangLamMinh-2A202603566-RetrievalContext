"""Shared helpers: data loading, evidence matching (same rule as Day 6), JSON I/O."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import config  # noqa: F401  (adds Day 6 starter to sys.path)
from src.ingestion import flatten  # Day 6 normalization, reused for identical hit definition


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def evidence_in(chunk: dict[str, Any], gold: list[dict[str, Any]]) -> bool:
    """Hit = chunk is on a gold (source_id, page) and contains the whole evidence string.

    Matching is case/whitespace-insensitive via Day 6 `flatten`. Gold items are alternatives.
    """
    text = flatten(chunk["text"])
    return any(chunk["source_id"] == g["source_id"] and int(chunk["page"]) == int(g["page"])
               and flatten(g["evidence"]) in text for g in gold)


def load_chunks() -> list[dict[str, Any]]:
    return read_json(config.CHUNKS_PATH)


def load_questions(split: str | None = None, answerable: bool | None = None) -> list[dict[str, Any]]:
    qs = read_json(config.QUESTIONS_PATH)
    return [q for q in qs if (split is None or q["split"] == split)
            and (answerable is None or q["answerable"] == answerable)]
