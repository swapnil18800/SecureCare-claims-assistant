"""Secret-handling helpers. Pure Python: no Streamlit import, no global state.

RULES THIS PROJECT FOLLOWS FOR THE LLM API KEY (OpenRouter / DeepSeek / OpenAI)
  1. The key lives only in the visitor's own Streamlit session (a widget value).
  2. It is passed explicitly to the LLM client; it is never written to os.environ,
     a module global, a file, a log line, the graph state, or any st.cache_* function.
  3. It is flushed from the session after every use (unless the visitor opts to keep it).
"""
from __future__ import annotations

import re

_KEY_PATTERN = re.compile(r"sk-[A-Za-z0-9_\-\*\.]{6,}")


def looks_like_api_key(value: str) -> bool:
    """Cheap sanity check; it does NOT verify the key. OpenRouter, DeepSeek and OpenAI keys all start 'sk-'."""
    value = (value or "").strip()
    return value.startswith("sk-") and len(value) >= 20 and " " not in value


def redact_secrets(text: str) -> str:
    """Mask anything that looks like an API key before text is shown or stored."""
    return _KEY_PATTERN.sub("sk-***", text or "")
