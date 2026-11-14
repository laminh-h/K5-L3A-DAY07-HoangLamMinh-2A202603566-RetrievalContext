"""Offline tests for day7 (no Gemini, no Chroma): BM25, RRF, context selection, agent loop with a fake LLM.

The fake LLM only exercises control flow; it is never used for benchmark numbers.
Skipped automatically when the Day 6 repo (needed for `flatten`) is not present.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    from day7.agent import run_agent
    from day7.context import select_context
    from day7.retrievers import BM25Retriever, HybridRRF, neighbors, tokenize
    from day7.common import evidence_in
    OK = True
except SystemExit:
    OK = False


def ch(cid, text, page=1, edition="2017-12"):
    return {"id": cid, "text": text, "source_id": "s", "source": "x.pdf", "page": page,
            "metadata": {"edition": edition}}


CHUNKS = [ch("A:s:p001:c00", "Credit growth target of 17 percent in 2018"),
          ch("A:s:p001:c01", "maintaining CPI below 4 percent"),
          ch("A:s:p002:c00", "Reserves reached US$63 billion", 2, "2018-06")]


class FakeRetriever:
    name = "fake"

    def __init__(self):
        self.calls = []

    def search(self, query, *, filters=None, top_k=3):
        self.calls.append((query, filters))
        return [{**c, "score": 1.0, "rank": i + 1} for i, c in enumerate(CHUNKS[:top_k])]


class FakeLLM:
    model = "fake"

    def __init__(self, script):
        self.script = list(script)

    def generate(self, **_):
        name, args = self.script.pop(0)
        return {"candidates": [{"content": {"role": "model", "parts": [{"functionCall": {"name": name, "args": args}}]}}],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 2}}


CFG = {"top_k": 2, "budget_chars": 10000, "max_searches": 2, "adjacent_tool": True}


@unittest.skipUnless(OK, "Day 6 repo not available")
class Day7Tests(unittest.TestCase):
    def test_tokenize_keeps_numbers(self):
        self.assertIn("4.25", tokenize("cut to 4.25 percent"))
        self.assertNotIn("the", tokenize("the rate"))

    def test_bm25_and_filter(self):
        bm = BM25Retriever(CHUNKS)
        self.assertEqual(bm.search("credit growth 17 percent", top_k=1)[0]["id"], "A:s:p001:c00")
        self.assertEqual([r["id"] for r in bm.search("percent", filters={"edition": "2018-06"})], [])
        with self.assertRaises(ValueError):
            bm.search("x", filters={"gold": 1})

    def test_rrf_fuses_ranks(self):
        class R:
            def __init__(self, ids): self.ids, self.name = ids, "r"
            def search(self, q, filters=None, top_k=3):
                return [{**next(c for c in CHUNKS if c["id"] == i), "score": 0, "rank": n + 1} for n, i in enumerate(self.ids)]
        h = HybridRRF(R(["A:s:p001:c00", "A:s:p001:c01"]), R(["A:s:p001:c01", "A:s:p002:c00"]))
        self.assertEqual(h.search("q", top_k=1)[0]["id"], "A:s:p001:c01")

    def test_context_budget_and_neighbors(self):
        by_id = {c["id"]: c for c in CHUNKS}
        self.assertEqual([c["id"] for c in neighbors("A:s:p001:c00", by_id)], ["A:s:p001:c01"])
        ctx = select_context([CHUNKS[0]], budget=10000, by_id=by_id, neighbor_window=1)
        self.assertEqual(len(ctx), 2)
        self.assertEqual(select_context(CHUNKS, budget=10), [])

    def test_evidence_match(self):
        self.assertTrue(evidence_in(CHUNKS[1], [{"source_id": "s", "page": 1, "evidence": "CPI  below 4"}]))
        self.assertFalse(evidence_in(CHUNKS[1], [{"source_id": "s", "page": 2, "evidence": "CPI below 4"}]))

    def test_agent_answers_with_valid_citation(self):
        llm = FakeLLM([("search_documents", {"query": "credit target"}),
                       ("submit_final", {"status": "answered", "answer": "17% [A:s:p001:c00]", "citations": ["A:s:p001:c00", "bogus"]})])
        r = FakeRetriever()
        out = run_agent("q?", llm=llm, retriever=r, by_id={}, cfg=CFG, filters={"edition": "2017-12"})
        self.assertEqual(out["status"], "answered")
        self.assertEqual(out["citations"], ["A:s:p001:c00"])
        self.assertEqual(r.calls[0][1], {"edition": "2017-12"})
        self.assertEqual(out["events"][-1]["invalid_citations"], ["bogus"])

    def test_agent_uncited_answer_becomes_abstain(self):
        llm = FakeLLM([("submit_final", {"status": "answered", "answer": "guess", "citations": []})])
        out = run_agent("q?", llm=llm, retriever=FakeRetriever(), by_id={}, cfg=CFG)
        self.assertEqual(out["status"], "abstain")

    def test_agent_search_limit_and_error(self):
        llm = FakeLLM([("search_documents", {"query": "a"})] * 3 + [("submit_final", {"status": "insufficient_evidence", "answer": "no", "citations": []})])
        out = run_agent("q?", llm=llm, retriever=FakeRetriever(), by_id={}, cfg=CFG)
        self.assertEqual(out["searches"], 2)
        self.assertTrue(any(e["event"] == "search_limit" for e in out["events"]))
        self.assertEqual(out["status"], "abstain")

        class Boom(FakeRetriever):
            def search(self, *a, **k): raise RuntimeError("store down")
        out = run_agent("q?", llm=FakeLLM([("search_documents", {"query": "a"})]), retriever=Boom(), by_id={}, cfg=CFG)
        self.assertEqual(out["status"], "error")


if __name__ == "__main__":
    unittest.main()
