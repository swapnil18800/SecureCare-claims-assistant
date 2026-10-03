"""Sidebar: provider + API key entry + model choice.

HOW THE KEY IS KEPT PRIVATE (the leak you may have seen in other Streamlit apps comes from
doing one of the things in the 'never' list):

  NEVER  os.environ["OPENAI_API_KEY"] = key      -> process-wide, every visitor shares it
  NEVER  @st.cache_resource / @st.cache_data      -> cached objects are shared by all sessions
  NEVER  a module-level global or a file          -> same process, same value for everyone
  NEVER  st.secrets for a visitor's own key       -> secrets are the app OWNER's, shared by all

  DO     keep the key in a widget bound to st.session_state (one dict per browser session)
  DO     pass it explicitly to build_llm(api_key=...) for ONE run, then drop the reference
  DO     flush it afterwards: we rotate the widget's key (nonce), so Streamlit discards the
         old widget and its value, and the next render shows an empty box

OWNER KEY (local use only): if .streamlit/secrets.toml holds e.g. OPENROUTER_API_KEY, it is used
when the visitor types no key. Never do this on a public deployment: every visitor would spend it.
"""
from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from securecare.config import DEFAULT_PROVIDER, PROVIDERS

KEY_PREFIX = "api_key_"


@dataclass
class Settings:
    provider: str
    model: str
    keep_key: bool


def _widget_name() -> str:
    return f"{KEY_PREFIX}{st.session_state.get('key_nonce', 0)}"


def get_api_key() -> str:
    """The key typed by THIS session's visitor ('' if none)."""
    return (st.session_state.get(_widget_name()) or "").strip()


def get_owner_key(provider: str) -> str:
    """The app owner's key for this provider from .streamlit/secrets.toml ('' if none)."""
    try:
        return str(st.secrets.get(PROVIDERS[provider]["secret_name"], "")).strip()
    except Exception:  # noqa: BLE001  (no secrets.toml at all)
        return ""


def resolve_api_key(settings: Settings) -> str:
    """The visitor's own key wins; otherwise fall back to the owner's key (local use only)."""
    return get_api_key() or get_owner_key(settings.provider)


def flush_api_key() -> None:
    """Rotate the widget key: the old widget (and the secret inside it) is discarded."""
    st.session_state["key_nonce"] = st.session_state.get("key_nonce", 0) + 1


def flush_key_after_use(settings: Settings) -> None:
    if not settings.keep_key:
        flush_api_key()


def render_sidebar() -> Settings:
    current = _widget_name()
    for stale in [k for k in st.session_state.keys() if k.startswith(KEY_PREFIX) and k != current]:
        del st.session_state[stale]            # make sure no old key survives in this session

    with st.sidebar:
        st.header("🔐 AI access")
        provider = st.selectbox(
            "Provider", list(PROVIDERS), index=list(PROVIDERS).index(DEFAULT_PROVIDER), key="provider",
            format_func=lambda name: PROVIDERS[name]["label"],
        )
        label = PROVIDERS[provider]["label"]
        st.text_input(
            f"{label} API key", type="password", key=current, placeholder="sk-...",
            help="Optional. Needed only for AI features: email autofill and AI-drafted letters.",
        )
        keep = st.checkbox(
            "Keep key for this browser session", value=False, key="keep_key",
            help="Off (recommended): the key is erased right after each AI action.",
        )
        st.button("Clear key now", on_click=flush_api_key, width="stretch")
        model = st.selectbox("Model", PROVIDERS[provider]["models"], key=f"model_{provider}")
        st.caption(
            "🔒 Your key exists only in **your** browser session. It is never saved, logged, cached "
            "or shared with other visitors, and it is erased after each use unless you tick *Keep*."
        )
        if not get_api_key():
            if get_owner_key(provider):
                st.info(f"No key typed: using the {label} key from `.streamlit/secrets.toml`.")
            else:
                st.info("No key? The claim workflow still runs. Letters use templates instead of AI.")
    return Settings(provider=provider, model=model, keep_key=keep)
