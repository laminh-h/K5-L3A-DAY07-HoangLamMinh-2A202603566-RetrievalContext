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


# Independent test set written 2026-11-14 AFTER configs/selected.json was frozen and committed
# (commit a5076c8). Pages were chosen so that none overlaps a dev/test gold page, and no Day 6 /
# Day 7 run had looked at them as a target. Run only with the frozen configs.
TEST2_ANSWERABLE = [
    {"id": "t01", "type": "direct",
     "question": "In 2010, what share of total health spending in Vietnam went on medicines?",
     "expected_answer": "43 percent of total health spending (2.7 percent of GDP), well above the OECD averages of 16 percent and 2 percent.",
     "gold": [{"source_id": "ts-2017-12", "page": 45, "evidence": "Spending on medicines in 2010 was 43 percent of total health spending or 2.7 percent of GDP"}]},
    {"id": "t02", "type": "paraphrase",
     "question": "After the 2016 drought and salinity intrusion, how quickly did Vietnam's agriculture, forestry and fishery sector recover?",
     "expected_answer": "Growth returned to 2.9 percent in 2017 and reached 4.1 percent in the first quarter of 2018.",
     "gold": [{"source_id": "ts-2018-06", "page": 19, "evidence": "Growth returned remarkably to 2.9 percent in 2017 and continued strongly at 4.1 percent in the first quarter 2018"}]},
    {"id": "t03", "type": "condition_exception",
     "question": "Besides central authorities, what shares of National Target Program funding came from local authorities and from community contributions?",
     "expected_answer": "26 percent from local authorities and 9 percent from community contributions (central authorities about 56 percent; donors 5, borrowing 4).",
     "gold": [{"source_id": "ts-2017-12", "page": 49, "evidence": "26 percent from local authorities; 5 percent from external donors; 4 percent from borrowing; and 9 percent from community contributions"}]},
    {"id": "t04", "type": "metadata_filter", "filter": {"edition": "2018-06"},
     "question": "What poverty rate at the US$3.2/day line is projected for Vietnam in 2018?",
     "expected_answer": "About 7.4 percent in 2018, down from about 10 percent in 2015 (around 6 percent by 2020).",
     "gold": [{"source_id": "ts-2018-06", "page": 32, "evidence": "projected to decline from about 10 percent in 2015 to 7.4 percent in 2018"}]},
    {"id": "t05", "type": "direct",
     "question": "What share of the overall public transport budget is spent on road transport?",
     "expected_answer": "Approximately 89 percent.",
     "gold": [{"source_id": "ts-2017-12", "page": 40, "evidence": "road transport represents approximately 89 percent of the overall public transport budget"}]},
]
TEST2_UNANSWERABLE = [
    {"id": "u05", "split": "test2",
     "question": "What was the average lending interest rate charged by Vietnamese commercial banks in 2018?",
     "absence_reason": "Reports discuss credit growth, policy rates and interbank rates but give no average lending rate.",
     "absence_check": "Regex 'lending' over all chunks: 1 match (2018-06 p21, lending volume +3.6% ytd); 'interest rate': 3 matches, none a lending-rate level."},
    {"id": "u06", "split": "test2",
     "question": "How many international tourist arrivals did Vietnam record in the first quarter of 2018?",
     "absence_reason": "2018-06 p16 only says services were 'supported by a higher number of tourist arrivals' without a figure; the 10.5 million figure (2017-12 p18) is for Jan-Oct 2017.",
     "absence_check": "Regex 'arrivals|entries|million (visitors|tourists|foreign)': 2 matches, 2017-12 p18 (Jan-Oct 2017) and 2018-06 p16 (no number)."},
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
    for q in TEST2_ANSWERABLE:
        for g in q["gold"]:
            if not any(evidence_in(c, [g]) for c in chunks):
                raise SystemExit(f"{q['id']}: gold not inside one chunk")
        out.append({"id": q["id"], "split": "test2", "type": q["type"], "answerable": True,
                    "expected_behavior": "search_and_answer", "question": q["question"],
                    "expected_answer": q["expected_answer"], "gold": q["gold"],
                    **({"filter": q["filter"]} if q.get("filter") else {})})
    for u in UNANSWERABLE + TEST2_UNANSWERABLE:
        out.append({**u, "type": "unanswerable", "answerable": False, "expected_behavior": "search_and_abstain"})
    # sanity: unanswerable absence regexes really have no hits
    write_json(config.QUESTIONS_PATH, out)
    write_json(config.CASES_PATH, [{"id": q["id"], "split": q["split"], "answerable": q["answerable"]} for q in out])
    write_json(config.DATA / "benchmark_build_report.json", {"dropped_gold_alternatives": dropped,
               "counts": {s: {"answerable": sum(q["split"] == s and q["answerable"] for q in out),
                              "unanswerable": sum(q["split"] == s and not q["answerable"] for q in out)}
                          for s in ("dev", "test", "test2")}})
    print(f"{len(out)} questions; dropped {len(dropped)} gold alternatives not inside one chunk: {dropped}")


if __name__ == "__main__":
    main()
