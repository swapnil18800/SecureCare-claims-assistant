"""LLM factory. The ONLY place a ChatOpenAI client is created.

OpenRouter, DeepSeek and OpenAI all speak the OpenAI chat API, so the provider only
changes `base_url` (see PROVIDERS in config.py).

SECURITY: never wrap `build_llm` (or anything that receives an api_key) in
st.cache_resource / st.cache_data / functools.lru_cache. Cached objects are shared
across every visitor of the app, which is exactly how keys leak between users.
"""
from __future__ import annotations

import time

from langchain_core.callbacks import BaseCallbackHandler
from langchain_openai import ChatOpenAI

from securecare.config import DEFAULT_MODEL, DEFAULT_PROVIDER, LLM_TIMEOUT_SECONDS, PROVIDERS
from securecare.logs import get_logger
from securecare.security import redact_secrets

log = get_logger("llm")


class _ToolCallingChatOpenAI(ChatOpenAI):
    """Structured output via tool calling: DeepSeek rejects OpenAI's json_schema response format."""

    def with_structured_output(self, schema=None, *, method="function_calling", **kwargs):
        return super().with_structured_output(schema, method=method, **kwargs)


class _LogLLMCalls(BaseCallbackHandler):
    """Logs provider, model, duration and token usage of each call. Never the prompt, reply or key."""

    def __init__(self, provider: str, model: str) -> None:
        self.label = f"{provider}/{model}"
        self.started: dict = {}

    def on_chat_model_start(self, serialized, messages, *, run_id, **kwargs) -> None:
        self.started[run_id] = time.perf_counter()
        log.info("LLM call started: %s", self.label)

    def on_llm_end(self, response, *, run_id, **kwargs) -> None:
        usage = (response.llm_output or {}).get("token_usage") or {}
        log.info("LLM call finished: %s in %.1fs, tokens=%s", self.label,
                 time.perf_counter() - self.started.pop(run_id, time.perf_counter()), usage.get("total_tokens"))

    def on_llm_error(self, error, *, run_id, **kwargs) -> None:
        log.warning("LLM call failed: %s after %.1fs: %s", self.label,
                    time.perf_counter() - self.started.pop(run_id, time.perf_counter()),
                    redact_secrets(f"{type(error).__name__}: {error}")[:300])


def build_llm(api_key: str, model: str = DEFAULT_MODEL, provider: str = DEFAULT_PROVIDER) -> ChatOpenAI:
    """Create a fresh, short-lived client. The key is passed explicitly, never via os.environ."""
    log.info("LLM client created: provider=%s model=%s", provider, model)
    return _ToolCallingChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=PROVIDERS[provider]["base_url"],
        temperature=0,
        timeout=LLM_TIMEOUT_SECONDS,
        max_retries=1,
        callbacks=[_LogLLMCalls(provider, model)],
    )
