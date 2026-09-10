"""Token-usage and timing instrumentation for the report pipeline (see main.py).

Groq's langchain integration (ChatGroq) follows the OpenAI-compatible response shape,
so per-call token usage comes back in response.llm_output["token_usage"]. This handler
accumulates that across every LLM call made through the ChatGroq instance it's attached
to (pass it via callbacks=[...] at construction so every agent that reuses that llm
instance is covered, not just the top-level call).

Cost is computed from Groq's own published pricing for the configured model (see
GROQ_PRICING_PER_MILLION_TOKENS below and the source cited next to it) -- not estimated.
"""
import time
from typing import Any, Dict, List, Optional

from langchain_core.callbacks import BaseCallbackHandler

# USD per 1,000,000 tokens. Source: https://console.groq.com/docs/model/openai/gpt-oss-120b
# (Groq's own published pricing page), checked 2026-09-10. Update this if GROQ_MODEL is
# overridden to something other than the default -- pricing is model-specific.
GROQ_PRICING_PER_MILLION_TOKENS = {
    "openai/gpt-oss-120b": {"input": 0.15, "output": 0.60},
}


class TokenUsageCallbackHandler(BaseCallbackHandler):
    """Records prompt/completion tokens and wall-clock time for every LLM call made
    through the ChatGroq instance this handler is attached to. Call `section_marker()`
    at the start of each report section to get a callable that returns just that
    section's calls, for a per-section breakdown."""

    def __init__(self):
        self.calls: List[Dict[str, Any]] = []
        self._start_times: Dict[Any, float] = {}

    def on_chat_model_start(self, serialized, messages, *, run_id, **kwargs):
        self._start_times[run_id] = time.perf_counter()

    def on_llm_start(self, serialized, prompts, *, run_id, **kwargs):
        self._start_times.setdefault(run_id, time.perf_counter())

    def on_llm_end(self, response, *, run_id, **kwargs):
        start = self._start_times.pop(run_id, None)
        elapsed = time.perf_counter() - start if start is not None else None
        usage = {}
        if response.llm_output:
            usage = response.llm_output.get("token_usage") or {}
        self.calls.append(
            {
                "elapsed_s": elapsed,
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }
        )

    def on_llm_error(self, error, *, run_id, **kwargs):
        self._start_times.pop(run_id, None)

    def calls_since(self, mark: int) -> List[Dict[str, Any]]:
        """Calls recorded after the given `len(self.calls)` snapshot -- use this to
        isolate one section's calls: `mark = len(handler.calls)` before the section,
        then `handler.calls_since(mark)` after."""
        return self.calls[mark:]

    @staticmethod
    def summarize(calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "n_calls": len(calls),
            "prompt_tokens": sum(c["prompt_tokens"] for c in calls),
            "completion_tokens": sum(c["completion_tokens"] for c in calls),
            "total_tokens": sum(c["total_tokens"] for c in calls),
            "llm_wall_clock_s": sum(c["elapsed_s"] for c in calls if c["elapsed_s"] is not None),
        }

    def total_summary(self) -> Dict[str, Any]:
        return self.summarize(self.calls)


def compute_cost_usd(prompt_tokens: int, completion_tokens: int, model: str) -> Optional[Dict[str, float]]:
    """Cost in USD from Groq's published per-model pricing. Returns None (rather than
    guessing) if the model isn't in GROQ_PRICING_PER_MILLION_TOKENS."""
    pricing = GROQ_PRICING_PER_MILLION_TOKENS.get(model)
    if pricing is None:
        return None
    input_cost = prompt_tokens / 1_000_000 * pricing["input"]
    output_cost = completion_tokens / 1_000_000 * pricing["output"]
    return {
        "input_cost_usd": round(input_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "total_cost_usd": round(input_cost + output_cost, 6),
        "input_price_per_million": pricing["input"],
        "output_price_per_million": pricing["output"],
    }
