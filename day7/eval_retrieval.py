"""Retrieval + static-context benchmark for each config. Writes summary and per-query traces.

Usage: python -m day7.eval_retrieval --split dev [--configs R1_dense R3_hybrid] [--file configs/retrieval.json]
Only answerable questions enter Hit@1 / Evidence Hit@3 / MRR / Context Evidence Rate.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from . import config
from .common import evidence_in, load_chunks, load_questions, read_json, write_json
from .context import context_chars, select_context
from .retrievers import build


def run_config(name: str, cfg: dict, questions: list[dict], chunks: list[dict], cache: dict) -> dict:
    retr = build(cfg["method"], chunks, cache)
    by_id = {c["id"]: c for c in chunks}
    traces, t_total = [], 0.0
    for q in questions:
        flt = q.get("filter") if cfg.get("use_filter") else None
        t0 = time.perf_counter()
        ranked = retr.search(q["question"], filters=flt, top_k=10)
        dt = time.perf_counter() - t0
        t_total += dt
        ctx = select_context(ranked[:cfg["context_k"]], budget=cfg["budget_chars"], by_id=by_id,
                             neighbor_window=cfg.get("neighbor_window", 0))
        hits = [evidence_in(h, q["gold"]) for h in ranked]
        first = next((i + 1 for i, h in enumerate(hits) if h), None)
        traces.append({
            "query_id": q["id"], "question": q["question"], "filter": flt, "latency_s": round(dt, 4),
            "first_hit_rank": first, "hit_at_1": bool(hits[:1] and hits[0]), "hit_at_3": any(hits[:3]),
            "context_evidence": any(evidence_in(c, q["gold"]) for c in ctx),
            "context_ids": [c["id"] for c in ctx], "context_chars": context_chars(ctx),
            "top10": [{"rank": h["rank"], "id": h["id"], "score": h["score"], "page": h["page"],
                       "edition": h["metadata"].get("edition"), "evidence_hit": e,
                       "text": h["text"][:240]} for h, e in zip(ranked, hits)],
        })
    n = len(traces)
    rate = lambda k: f"{sum(t[k] for t in traces)}/{n}"
    return {
        "config": name, **{k: v for k, v in cfg.items() if k != "hypothesis"}, "hypothesis": cfg.get("hypothesis"),
        "N": n, "hit_at_1": rate("hit_at_1"), "evidence_hit_at_3": rate("hit_at_3"),
        "mrr_at_10": round(sum(1 / t["first_hit_rank"] for t in traces if t["first_hit_rank"]) / n, 3),
        "recall_at_10": f"{sum(t['first_hit_rank'] is not None for t in traces)}/{n}",
        "context_evidence_rate": rate("context_evidence"),
        "avg_context_chars": round(sum(t["context_chars"] for t in traces) / n),
        "retrieval_latency_ms_per_query": round(1000 * t_total / n, 1),
        "cost_usd": 0.0, "traces": traces,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "test"], default="dev")
    ap.add_argument("--file", type=Path, default=config.ROOT / "configs" / "retrieval.json")
    ap.add_argument("--configs", nargs="*")
    args = ap.parse_args()
    cfgs = read_json(args.file)["configs"]
    if args.split == "test":
        selected = read_json(config.ROOT / "configs" / "selected.json")
        allowed = {selected["baseline"], selected["selected"]}
        names = args.configs or sorted(allowed)
        if set(names) - allowed:
            raise SystemExit(f"test chỉ chạy config đã chốt trong configs/selected.json: {sorted(allowed)}")
    else:
        names = args.configs or list(cfgs)
    chunks = load_chunks()
    questions = load_questions(args.split, answerable=True)
    cache: dict = {}
    out_dir = config.RESULTS / "retrieval" / args.split
    rows = []
    for name in names:
        res = run_config(name, cfgs[name], questions, chunks, cache)
        write_json(out_dir / f"{name}.json", res)
        rows.append({k: v for k, v in res.items() if k != "traces"})
        print(f"{name:18s} H@1 {res['hit_at_1']:6s} H@3 {res['evidence_hit_at_3']:6s} MRR {res['mrr_at_10']:.3f} "
              f"R@10 {res['recall_at_10']:6s} CER {res['context_evidence_rate']:6s} "
              f"ctx {res['avg_context_chars']}c  {res['retrieval_latency_ms_per_query']}ms")
    prev = out_dir / "summary.json"
    merged = {r["config"]: r for r in (read_json(prev) if prev.exists() else [])}
    merged.update({r["config"]: r for r in rows})
    write_json(prev, list(merged.values()))


if __name__ == "__main__":
    main()
