"""LLM factory. The ONLY place a ChatOpenAI client is created.

OpenRouter, DeepSeek and OpenAI all speak the OpenAI chat API, so the provider only
changes `base_url` (see PROVIDERS in config.py).

SECURITY: never wrap `build_llm` (or anything that receives an api_key) in
st.cache_resource / st.cache_data / functools.lru_cache. Cached objects are shared
across every visitor of the app, which is exactly how keys leak between users.
"""
from __future__ import annotations

from langchain_openai import ChatOpenAI

from securecare.config import DEFAULT_MODEL, DEFAULT_PROVIDER, LLM_TIMEOUT_SECONDS, PROVIDERS


class _ToolCallingChatOpenAI(ChatOpenAI):
    """Structured output via tool calling: DeepSeek rejects OpenAI's json_schema response format."""

    def with_structured_output(self, schema=None, *, method="function_calling", **kwargs):
        return super().with_structured_output(schema, method=method, **kwargs)


def build_llm(api_key: str, model: str = DEFAULT_MODEL, provider: str = DEFAULT_PROVIDER) -> ChatOpenAI:
    """Create a fresh, short-lived client. The key is passed explicitly, never via os.environ."""
    return _ToolCallingChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=PROVIDERS[provider]["base_url"],
        temperature=0,
        timeout=LLM_TIMEOUT_SECONDS,
        max_retries=1,
    )
