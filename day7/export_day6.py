"""Export the Day 6 Chroma collection to the Day 7 chunk JSON contract (data/chunks.json).

Reads ids/text/metadata straight from the persisted Day 6 store; vectors stay in Chroma and are
queried live by the dense retriever. No text is re-chunked or edited.
"""
from __future__ import annotations

import json

from . import config


def main() -> None:
    import chromadb

    client = chromadb.PersistentClient(path=str(config.CHROMA_PATH))
    col = client.get_collection(f"day6_index_{config.DAY6_INDEX}")
    got = col.get(include=["documents", "metadatas"])
    chunks = []
    for cid, text, meta in zip(got["ids"], got["documents"], got["metadatas"]):
        meta = dict(meta or {})
        chunks.append({
            "id": cid, "text": text, "source_id": meta.pop("document_id"),
            "source": meta.pop("source"), "page": int(meta.pop("page")), "metadata": meta,
        })
    chunks.sort(key=lambda c: (c["source_id"], c["page"], c["metadata"].get("char_start", 0)))
    config.DATA.mkdir(exist_ok=True)
    config.CHUNKS_PATH.write_text(json.dumps(chunks, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(chunks)} chunks from {col.name} ({col.metadata}) -> {config.CHUNKS_PATH}")


if __name__ == "__main__":
    main()
