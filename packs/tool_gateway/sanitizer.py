"""Output sanitizer for Tool Gateway Pack — v0.1.

Strips common sensitive patterns from capability result output before
storing in CapabilityResult and sourcing to Core.

Patterns redacted:
  - API key patterns (sk-, pk-, Bearer tokens)
  - Long hexadecimal strings (potential tokens/hashes)
  - Password field values in JSON-like strings
  - AWS access keys (AKIA...)
  - Private key blocks (-----BEGIN ...)

All matches are replaced with [REDACTED:<reason>] so the redaction
is visible in the output — silent stripping would hide data loss.
"""

from __future__ import annotations

import re

# Ordered list of (pattern, replacement) — applied left to right
_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Private key blocks (PEM format)
    (
        re.compile(r"-----BEGIN [A-Z ]+-----[\s\S]*?-----END [A-Z ]+-----", re.MULTILINE),
        "[REDACTED:private_key_block]",
    ),
    # AWS access key IDs
    (
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "[REDACTED:aws_access_key]",
    ),
    # OpenAI / Anthropic / generic API key patterns (sk-, pk-, sk_live_, etc.)
    (
        re.compile(r"\b(sk|pk|rk|ak|sk_live|sk_test|pk_live|pk_test)-[a-zA-Z0-9_\-]{20,}"),
        "[REDACTED:api_key]",
    ),
    # Bearer tokens in Authorization headers or JSON values
    (
        re.compile(r"(Bearer\s+|\"?authorization\"?\s*:\s*\"?Bearer\s+)[a-zA-Z0-9\-_=+/]{20,}", re.IGNORECASE),
        "[REDACTED:bearer_token]",
    ),
    # Long hex strings (32+ chars) that look like tokens/secrets
    (
        re.compile(r"\b[0-9a-fA-F]{32,}\b"),
        "[REDACTED:hex_token]",
    ),
    # password/secret/token field values in JSON-like text
    (
        re.compile(
            r'"(password|secret|token|api_key|apikey|access_token|refresh_token|private_key)"'
            r'\s*:\s*"[^"]{4,}"',
            re.IGNORECASE,
        ),
        "[REDACTED:sensitive_field]",
    ),
]


def sanitize_output(text: str) -> tuple[str, bool]:
    """Sanitize a capability result output string.

    Applies all sensitive pattern redactions in order.

    Args:
        text: Raw output string from capability execution.

    Returns:
        Tuple of (sanitized_text, was_modified).
        was_modified=True means at least one pattern was redacted.
    """
    result = text
    for pattern, replacement in _PATTERNS:
        result = pattern.sub(replacement, result)
    return result, (result != text)
