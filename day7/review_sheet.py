"""Write a human review sheet (markdown) for an agent run: question, expected answer, gold evidence,
agent answer, and the FULL text of every cited chunk, so each citation can be read and judged.

Usage: python -m day7.review_sheet --split dev --config A1_dense
Then labels go to results/agent/<split>/<config>/reviews.json (answer_grade / citation_support /
abstention_correct + reason) and are aggregated by starter/agent_metrics.py.
"""
from __future__ import annotations

import argparse

from . import config
from .common import load_chunks, load_questions, read_json


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev")
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    d = config.RESULTS / "agent" / args.split / args.config
    by_id = {c["id"]: c for c in load_chunks()}
    qs = {q["id"]: q for q in load_questions(args.split)}
    lines = [f"# Review sheet - {args.config} / {args.split}\n"]
    for t in read_json(d / "traces.json"):
        q = qs[t["query_id"]]
        lines.append(f"## {t['query_id']} ({q['type']}) - status `{t['status']}`\n")
        lines.append(f"**Q:** {q['question']}  ")
        if q.get("filter"):
            lines.append(f"**User filter:** {q['filter']}  ")
        if q["answerable"]:
            lines.append(f"**Expected:** {q['expected_answer']}  ")
            lines.append("**Gold:** " + "; ".join(f"{g['source_id']} p{g['page']}: \"{g['evidence']}\"" for g in q["gold"]) + "  ")
            lines.append(f"**Auto:** {t.get('auto')}  ")
        else:
            lines.append(f"**Expected:** abstain - {q['absence_reason']}  ")
        queries = [e.get("query") or e.get("chunk_id") for e in t["events"] if e["event"] == "search"]
        lines.append(f"**Searches ({len(queries)}):** {queries}  ")
        lines.append(f"**Answer:** {t['answer'] or t.get('error', '')}  ")
        for c in t["citations"]:
            ch = by_id[c]
            lines.append(f"\n> **[{c}]** {ch['source_id']} p{ch['page']}: {ch['text']}")
        lines.append("")
    (d / "review_sheet.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(d / "review_sheet.md")


if __name__ == "__main__":
    main()
