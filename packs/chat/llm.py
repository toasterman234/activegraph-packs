"""Chat Adapter Pack — native LLM wiring.

This module connects the Chat Pack to ActiveGraph's *native* LLM layer
(``activegraph.llm``) rather than hand-rolling provider HTTP calls.

Pieces:

  ChatReply           — the structured output schema for chat_llm_responder.
                        The model returns ``{"reply": "..."}`` and the
                        behavior writes ``reply`` onto the ChatTurn.

  MockChatProvider    — a scripted ``LLMProvider`` used when no real provider
                        key is configured. It runs the full chat pipeline
                        end-to-end (so the demo / fixtures work with no API
                        key) and its reply explains how to enable a real LLM.

  select_chat_provider — inspects the environment and returns the right
                        provider instance (OpenAIProvider / AnthropicProvider
                        when a key is present, MockChatProvider otherwise) plus
                        an info dict describing the resolved configuration.

SECURITY: API keys are read from the environment by the native providers at
call time. They are never written to the graph, events, logs, or artifacts.
The Secrets Pack records name-only CredentialRefs for auditability.
"""

from __future__ import annotations

import json
import os
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field

from activegraph.llm import AnthropicProvider, LLMResponse, OpenAIProvider


# ================================================================ Output schema


class ChatReply(BaseModel):
    """Structured output for chat_llm_responder.

    A single free-text assistant reply. Kept deliberately minimal so the
    model's job is unambiguous: produce the assistant's next message.
    """

    reply: str = Field(
        description="The assistant's reply to the user's most recent message.",
    )


# ================================================================ Provider config

# Native ActiveGraph providers, keyed by the short provider id used in
# settings / the config API. OpenRouter is intentionally omitted for now
# (no native provider) — it is a planned follow-up via an OpenAI-compatible
# adapter.
_PROVIDER_KEY_ENV: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}

# Order used when auto-detecting which provider to use from the environment.
_AUTODETECT_ORDER = ["openai", "anthropic"]

# Provider ids that have a native ActiveGraph provider implementation.
SUPPORTED_PROVIDERS = list(_PROVIDER_KEY_ENV.keys())


def provider_key_env(provider: str) -> Optional[str]:
    """Return the env var name a provider's API key is read from, or None."""
    return _PROVIDER_KEY_ENV.get((provider or "").strip().lower())


_DEFAULT_MOCK_NOTE = (
    "I'm running in mock mode, so this is a canned reply — but the full "
    "ActiveGraph chat pipeline did run end-to-end (ingest \u2192 comm message "
    "\u2192 responder \u2192 turn), only the LLM itself is stubbed.\n\n"
    "To get real answers, add a provider API key:\n"
    "  \u2022 OPENAI_API_KEY \u2014 use OpenAI\n"
    "  \u2022 ANTHROPIC_API_KEY \u2014 use Anthropic\n\n"
    "Set it as an environment variable / Replit Secret, or add it on the "
    "Secrets page in this Inspector. As soon as a key is detected, chat "
    "upgrades to live mode automatically."
)


class MockChatProvider:
    """A scripted ``LLMProvider`` for the no-API-key path.

    Implements the ``activegraph.llm.LLMProvider`` protocol surface so the
    runtime's native LLM lifecycle (``llm.requested`` \u2192 provider \u2192
    ``llm.responded``) works unchanged — the only difference is that the
    completion is canned instead of a network call.

    The reply is the same instructive text every time, which keeps fixtures
    deterministic while telling demo users exactly how to enable a real LLM.
    """

    # @llm_behavior(model=None) resolves to this at registration / first run.
    default_model: str = "mock-chat-1"

    def __init__(self, *, note: Optional[str] = None) -> None:
        self._note = note or _DEFAULT_MOCK_NOTE

    def complete(
        self,
        *,
        system: str,
        messages: list,
        model: str,
        max_tokens: int,
        temperature: float,
        top_p: float,
        output_schema: Optional[type],
        timeout_seconds: float,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> LLMResponse:
        text = self._note
        parsed: Any = None
        if output_schema is not None:
            try:
                parsed = output_schema(reply=text)
            except Exception:
                # Unknown schema shape — leave parsed=None; raw_text still set.
                parsed = None
        return LLMResponse(
            raw_text=json.dumps({"reply": text}),
            parsed=parsed,
            input_tokens=0,
            output_tokens=0,
            cost_usd=Decimal("0"),
            latency_seconds=0.0,
            model=model or self.default_model,
            finish_reason="stop",
        )

    def estimate_cost(
        self, *, input_tokens: int, output_tokens: int, model: str
    ) -> Decimal:
        return Decimal("0")

    def count_tokens(self, *, system: str, messages: list, model: str) -> int:
        return 0

    def recognizes_model(self, name: str) -> bool:
        # Permissive: the mock serves any model name.
        return True


def _make_native_provider(provider: str, model: Optional[str]):
    """Construct a native provider, pinning ``model`` as its default_model.

    chat_llm_responder is declared with ``model=None`` so the runtime resolves
    the model from the provider's ``default_model`` at call time. Setting it on
    the instance lets users choose a model (env / Secrets page) without the
    behavior pinning a provider-specific name at import time.
    """
    if provider == "openai":
        inst: Any = OpenAIProvider()
    elif provider == "anthropic":
        inst = AnthropicProvider()
    else:  # pragma: no cover - guarded by callers
        raise ValueError(f"no native provider for {provider!r}")
    if model:
        inst.default_model = model
    return inst


def resolve_chat_config(
    *,
    provider_pref: Optional[str] = None,
    model: Optional[str] = None,
) -> dict[str, Any]:
    """Resolve the effective chat LLM configuration from args + environment.

    Precedence: explicit args > ``CHAT_LLM_PROVIDER`` / ``CHAT_LLM_MODEL`` env
    > auto-detection from whichever provider key is present in the environment.

    Returns an info dict (never the secret value):
      mode:        "live" | "mock"
      provider:    resolved provider id ("openai" | "anthropic" | "mock")
      model:       effective model name (None in mock mode)
      key_env:     env var the key is read from (None in mock mode)
      key_present: whether that env var is set
    """
    pref = (provider_pref or os.environ.get("CHAT_LLM_PROVIDER") or "").strip().lower()
    model = (model or os.environ.get("CHAT_LLM_MODEL") or "").strip() or None

    chosen: Optional[str] = None
    if pref in _PROVIDER_KEY_ENV:
        if os.environ.get(_PROVIDER_KEY_ENV[pref]):
            chosen = pref
    if chosen is None and pref in ("", "auto", "mock"):
        for p in _AUTODETECT_ORDER:
            if os.environ.get(_PROVIDER_KEY_ENV[p]):
                chosen = p
                break

    if chosen is None:
        return {
            "mode": "mock",
            "provider": "mock",
            "model": None,
            "key_env": _PROVIDER_KEY_ENV.get(pref),
            "key_present": False,
            "requested_provider": pref or "auto",
        }

    key_env = _PROVIDER_KEY_ENV[chosen]
    eff_model = model or (
        "gpt-4o-mini" if chosen == "openai" else "claude-sonnet-4-5"
    )
    return {
        "mode": "live",
        "provider": chosen,
        "model": eff_model,
        "key_env": key_env,
        "key_present": True,
        "requested_provider": pref or "auto",
    }


def select_chat_provider(
    *,
    provider_pref: Optional[str] = None,
    model: Optional[str] = None,
) -> tuple[Any, dict[str, Any]]:
    """Return ``(provider_instance, info)`` for the resolved chat config.

    ``info`` is the dict from :func:`resolve_chat_config`. The provider is a
    native ActiveGraph provider in live mode, or :class:`MockChatProvider`
    otherwise.
    """
    info = resolve_chat_config(provider_pref=provider_pref, model=model)
    if info["mode"] == "live":
        provider = _make_native_provider(info["provider"], info["model"])
    else:
        provider = MockChatProvider()
    return provider, info
