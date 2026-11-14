"""Context selection: dedup, rank order, optional same-page neighbor expansion, char budget."""
from __future__ import annotations

from typing import Any

from .retrievers import neighbors


def format_chunk(c: dict[str, Any]) -> str:
    return f"[{c['id']}] (source: {c['source_id']}, edition {c['metadata'].get('edition')}, page {c['page']})\n{c['text']}"


def select_context(candidates: list[dict[str, Any]], *, budget: int, by_id: dict[str, dict[str, Any]] | None = None,
                   neighbor_window: int = 0) -> list[dict[str, Any]]:
    """Greedy in candidate order. A chunk that does not fit is skipped (later, shorter ones may fit).

    With neighbor_window>0 each selected chunk pulls its adjacent same-page chunks right after it,
    because Day 6 index A uses 500-char windows that often cut a claim from its number.
    """
    chosen: list[dict[str, Any]] = []
    seen: set[str] = set()
    used = 0

    def add(c: dict[str, Any]) -> bool:
        nonlocal used
        if c["id"] in seen:
            return False
        size = len(format_chunk(c))
        if used + size > budget:
            return False
        chosen.append(c)
        seen.add(c["id"])
        used += size
        return True

    for c in candidates:
        if add(c) and neighbor_window and by_id is not None:
            for n in neighbors(c["id"], by_id, neighbor_window):
                add(n)
    return chosen


def context_chars(chunks: list[dict[str, Any]]) -> int:
    return sum(len(format_chunk(c)) for c in chunks)
