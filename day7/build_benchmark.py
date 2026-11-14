"""Build data/questions.json (+ data/cases.json) from the Day 6 benchmark plus 4 unanswerable questions.

Day 6 answerable questions keep their split (15 dev / 5 test, fixed before any Day 6 run; Day 6
never tuned on test). Each Day 6 gold item is kept only if its evidence lies wholly inside one
chunk of the Day 6 index used here; dropped alternatives are reported. Unanswerable questions
were written near-topic and checked against the full corpus (see `absence_check`).
"""
from __future__ import annotations

from . import config
from .common import evidence_in, load_chunks, read_json, write_json

UNANSWERABLE = [
    {"id": "u01", "split": "dev",
     "question": "What was Vietnam's official unemployment rate in 2017?",
     "absence_reason": "Both reports discuss job creation, wages and labor demand but never state an unemployment rate.",
     "absence_check": "Regex 'unemployment rate|jobless' over all 618 chunks: 0 matches; 'unemploy' only appears as a chart legend for unemployment benefits (2017-12 p54-55)."},
    {"id": "u02", "split": "dev",
     "question": "What sovereign credit rating did Moody's or Fitch assign to Vietnam in 2018?",
     "absence_reason": "Reports cover public debt and bond yields but no rating agency action.",
     "absence_check": "Regex 'credit rating|sovereign rating|Moody|Fitch' over all chunks: 0 matches ('S&P' only as 'S&P 500' chart legend)."},
    {"id": "u03", "split": "test",
     "question": "What regional minimum wage did Vietnam set for 2018?",
     "absence_reason": "Reports describe average nominal/real wage growth, not the statutory minimum wage.",
     "absence_check": "Regex 'minimum wage' over all chunks: 0 matches; 'wage' passages (2017-12 p19, 2018-06 p18) are averages."},
    {"id": "u04", "split": "test",
     "question": "By what percentage did Vietnam raise the retail electricity tariff in 2017?",
     "absence_reason": "'Electricity' only appears in Doing Business 'Getting Electricity' reform text; no retail tariff change is reported.",
     "absence_check": "Regex 'electricity' over all chunks: 8 matches, all Doing Business indicators (2017-12 p33); 'tariff' matches concern trade tariffs."},
]


def main() -> None:
    chunks = load_chunks()
    day6 = read_json(config.DAY6_ROOT / "benchmark" / "questions.json")["questions"]
    out, dropped = [], []
    for q in day6:
        gold = []
        for g in q["gold"]:
            item = {"source_id": g["source_id"], "page": g["page"], "evidence": g["evidence_quote"]}
            (gold if any(evidence_in(c, [item]) for c in chunks) else dropped).append(
                item if any(evidence_in(c, [item]) for c in chunks) else {"id": q["id"], **item})
        if not gold:
            raise SystemExit(f"{q['id']}: no gold evidence fits a single chunk")
        rec = {"id": q["id"], "split": q["split"], "type": q["type"], "answerable": True,
               "expected_behavior": "search_and_answer", "question": q["question"],
               "expected_answer": q["expected_answer"], "gold": gold}
        if q.get("filter"):
            rec["filter"] = q["filter"]
        out.append(rec)
    for u in UNANSWERABLE:
        out.append({**u, "type": "unanswerable", "answerable": False, "expected_behavior": "search_and_abstain"})
    # sanity: unanswerable absence regexes really have no hits
    write_json(config.QUESTIONS_PATH, out)
    write_json(config.CASES_PATH, [{"id": q["id"], "split": q["split"], "answerable": q["answerable"]} for q in out])
    write_json(config.DATA / "benchmark_build_report.json", {"dropped_gold_alternatives": dropped,
               "counts": {s: {"answerable": sum(q["split"] == s and q["answerable"] for q in out),
                              "unanswerable": sum(q["split"] == s and not q["answerable"] for q in out)}
                          for s in ("dev", "test")}})
    print(f"{len(out)} questions; dropped {len(dropped)} gold alternatives not inside one chunk: {dropped}")


if __name__ == "__main__":
    main()
