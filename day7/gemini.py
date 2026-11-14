"""Minimal Gemini REST client (generateContent + function calling). Key from GEMINI_API_KEY.

No SDK dependency: uses `requests`. Retries 429/5xx with backoff; other errors raise.
"""
from __future__ import annotations

import os
import time
from typing import Any

import requests

from . import config

URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
# USD per 1M tokens (list price, paid tier) - used only to estimate cost; free tier bills 0.
PRICE_IN = float(os.getenv("GEMINI_PRICE_IN_PER_M") or 0.30)
PRICE_OUT = float(os.getenv("GEMINI_PRICE_OUT_PER_M") or 2.50)
MIN_INTERVAL = float(os.getenv("GEMINI_MIN_INTERVAL_S") or 4.0)


class GeminiError(RuntimeError):
    pass


class Gemini:
    def __init__(self, model: str | None = None, thinking_budget: int | None = 0, temperature: float = 0.0):
        self.key = os.getenv("GEMINI_API_KEY")
        if not self.key:
            raise GeminiError("Thiếu GEMINI_API_KEY trong .env (xem .env.example)")
        self.model = model or config.GEMINI_MODEL
        self.thinking_budget = thinking_budget
        self.temperature = temperature
        self._last = 0.0

    def generate(self, *, system: str, contents: list[dict[str, Any]], tools: list[dict[str, Any]],
                 max_retries: int = 6) -> dict[str, Any]:
        gen: dict[str, Any] = {"temperature": self.temperature}
        if self.thinking_budget is not None:
            gen["thinkingConfig"] = {"thinkingBudget": self.thinking_budget}
        body = {"systemInstruction": {"parts": [{"text": system}]}, "contents": contents,
                "tools": [{"functionDeclarations": tools}],
                "toolConfig": {"functionCallingConfig": {"mode": "ANY"}},
                "generationConfig": gen}
        delay = 5.0
        for attempt in range(max_retries + 1):
            wait = MIN_INTERVAL - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            r = requests.post(URL.format(model=self.model), json=body, timeout=180,
                              headers={"x-goog-api-key": self.key, "Content-Type": "application/json"})
            if r.status_code == 200:
                data = r.json()
                if not data.get("candidates"):
                    raise GeminiError(f"no candidates: {str(data)[:300]}")
                return data
            if r.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                retry = delay
                try:
                    for d in r.json().get("error", {}).get("details", []):
                        if "retryDelay" in d:
                            retry = max(retry, float(d["retryDelay"].rstrip("s")) + 1)
                except Exception:
                    pass
                time.sleep(min(retry, 90))
                delay *= 2
                continue
            raise GeminiError(f"HTTP {r.status_code}: {r.text[:400]}")
        raise GeminiError("retries exhausted")

    @staticmethod
    def usage(resp: dict[str, Any]) -> dict[str, int]:
        u = resp.get("usageMetadata", {})
        return {"input": int(u.get("promptTokenCount", 0)),
                "output": int(u.get("candidatesTokenCount", 0)) + int(u.get("thoughtsTokenCount", 0))}

    @staticmethod
    def cost(tokens_in: int, tokens_out: int) -> float:
        return tokens_in / 1e6 * PRICE_IN + tokens_out / 1e6 * PRICE_OUT
