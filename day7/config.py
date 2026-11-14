"""Paths and settings for Day 7. Day 6 code, Chroma store and embedding model are reused as-is."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_env() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env()

DAY6_ROOT = Path(os.getenv("DAY6_ROOT") or ROOT.parent / "K5-L3A-DAY06-HoangLamMinh-2A202603566-DataIngestion")
DAY6_STARTER = DAY6_ROOT / "starter"
CHROMA_PATH = Path(os.getenv("CHROMA_PATH") or DAY6_STARTER / "chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL") or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DAY6_INDEX = os.getenv("DAY6_INDEX") or "A"  # strategy A was the Day 6 selected configuration
RERANK_MODEL = os.getenv("RERANK_MODEL") or "cross-encoder/ms-marco-MiniLM-L-6-v2"
GEMINI_MODEL = os.getenv("GEMINI_MODEL") or "gemini-3.5-flash-lite"

DATA = ROOT / "data"
CHUNKS_PATH = DATA / "chunks.json"
QUESTIONS_PATH = DATA / "questions.json"
CASES_PATH = DATA / "cases.json"
RESULTS = ROOT / "results"

if not DAY6_STARTER.exists():
    raise SystemExit(f"Không tìm thấy Day 6 tại {DAY6_ROOT}; đặt biến DAY6_ROOT")
if str(DAY6_STARTER) not in sys.path:
    sys.path.insert(0, str(DAY6_STARTER))
