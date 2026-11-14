"""Run the agent on a split and save traces + automatic (gold-based, post-hoc) context metrics.

Usage: python -m day7.run_agent_bench --config A1_dense --split dev [--ids q01 u01]
Gold is only read AFTER the agent finished each question, to compute Context Evidence / Hit.
"""
from __future__ import annotations

import argparse
from collections import Counter

from . import config
from .common import evidence_in, load_chunks, load_questions, read_json, write_json
from .gemini import Gemini
from .agent import run_agent
from .retrievers import build


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--split", choices=["dev", "test", "test2"], default="dev")
    ap.add_argument("--ids", nargs="*")
    args = ap.parse_args()
    cfg = read_json(config.ROOT / "configs" / "agent.json")["configs"][args.config]
    if args.split in ("test", "test2"):
        sel = read_json(config.ROOT / "configs" / "selected.json")
        if args.config not in (sel["agent_baseline"], sel["agent_selected"]):
            raise SystemExit("test chỉ chạy agent config đã chốt trong configs/selected.json")
    chunks = load_chunks()
    by_id = {c["id"]: c for c in chunks}
    retriever = build(cfg["method"], chunks, {})
    llm = Gemini(thinking_budget=cfg.get("thinking_budget"))
    questions = [q for q in load_questions(args.split) if not args.ids or q["id"] in args.ids]
    out_dir = config.RESULTS / "agent" / args.split / args.config
    path = out_dir / "traces.json"
    prev = {t["query_id"]: t for t in read_json(path)} if path.exists() else {}
    for q in questions:
        public = {"question": q["question"], "filters": q.get("filter")}  # nothing else reaches the agent
        res = run_agent(public["question"], llm=llm, retriever=retriever, by_id=by_id, cfg=cfg, filters=public["filters"])
        rec = {"query_id": q["id"], "split": q["split"], "answerable": q["answerable"], "question": q["question"],
               "config": args.config, **res}
        if q["answerable"]:  # post-hoc, gold-based
            ctx = [by_id[i] for i in res["context_ids"]]
            first = next((e for e in res["events"] if e["event"] == "search" and e.get("tool") == "search_documents"), None)
            rec["auto"] = {
                "context_evidence": any(evidence_in(c, q["gold"]) for c in ctx),
                "first_search_hit_at_3": bool(first and any(evidence_in(by_id[r["id"]], q["gold"]) for r in first["results"][:3])),
                "cited_evidence_chunk": any(evidence_in(by_id[c], q["gold"]) for c in res["citations"]),
            }
        prev[q["id"]] = rec
        print(f"{q['id']} {res['status']:8s} searches={res['searches']} calls={res['llm_calls']} "
              f"{res['latency_s']}s cites={res['citations']} {rec.get('auto', '')} | {res['answer'][:110]!r}"
              + (f" ERROR {res.get('error')}" if res["status"] == "error" else ""), flush=True)
    traces = sorted(prev.values(), key=lambda t: t["query_id"])
    write_json(path, traces)
    ok = [t for t in traces if t["status"] != "error"]
    ans = [t for t in traces if t["answerable"]]
    summary = {
        "config": args.config, "split": args.split, **cfg, "model": llm.model, "N": len(traces),
        "status": dict(Counter(t["status"] for t in traces)), "provider_errors": len(traces) - len(ok),
        "tool_use": f"{sum(t['searches'] > 0 for t in ok)}/{len(ok)}",
        "searches_distribution": dict(sorted(Counter(t["searches"] for t in ok).items())),
        "llm_calls_distribution": dict(sorted(Counter(t["llm_calls"] for t in ok).items())),
        "context_evidence_rate": f"{sum(t['auto']['context_evidence'] for t in ans)}/{len(ans)}",
        "first_search_hit_at_3": f"{sum(t['auto']['first_search_hit_at_3'] for t in ans)}/{len(ans)}",
        "auto_cited_gold_chunk": f"{sum(t['auto']['cited_evidence_chunk'] for t in ans)}/{len(ans)}",
        "abstained_unanswerable": f"{sum(t['status'] == 'abstain' for t in traces if not t['answerable'])}/{sum(not t['answerable'] for t in traces)}",
        "abstained_answerable": f"{sum(t['status'] == 'abstain' for t in ans)}/{len(ans)}",
        "avg_context_chars": round(sum(t["context_chars"] for t in ok) / max(1, len(ok))),
        "avg_latency_s": round(sum(t["latency_s"] for t in ok) / max(1, len(ok)), 2),
        "tokens_in": sum(t["tokens_in"] for t in traces), "tokens_out": sum(t["tokens_out"] for t in traces),
        "est_cost_usd_list_price": round(sum(t["cost_usd"] for t in traces), 5),
    }
    write_json(out_dir / "auto_summary.json", summary)
    print(summary)


if __name__ == "__main__":
    main()
