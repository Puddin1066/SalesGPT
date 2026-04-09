"""
Strip common .env mistakes from Zoho OAuth values (inline # comments, tabs, extra words).

ZOHO_CLIENT_ID must be a single token (e.g. 1000.xxxxx). Users sometimes paste:
  1000.xxx<TAB># OAuth client ID from ...
which breaks authorize URLs.
"""
from __future__ import annotations


def clean_zoho_client_id(raw: str) -> tuple[str, str]:
    """
    Returns (client_id, warning_message).

    warning_message is non-empty if the raw value was trimmed.
    """
    s = (raw or "").strip()
    if not s:
        return "", ""
    before = s
    s = s.split("#", 1)[0].strip()
    parts = s.split()
    out = parts[0] if parts else ""
    if not out:
        return "", ""
    msg = ""
    if before.strip() != out:
        msg = (
            "ZOHO_CLIENT_ID contained extra text (e.g. # comment or tab). "
            "Use a single line: ZOHO_CLIENT_ID=1000.xxxxx — no comments on the same line."
        )
    return out, msg


def clean_zoho_secret_or_token(raw: str) -> tuple[str, str]:
    """Strip trailing # comment from one line; do not split on spaces (secrets can be one token)."""
    s = (raw or "").strip()
    if not s:
        return "", ""
    before = s
    s = s.split("#", 1)[0].strip()
    msg = ""
    if before != s:
        msg = "Value had an inline # comment; only the part before # was kept. Prefer moving comments to their own line."
    return s, msg
