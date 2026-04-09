"""Minimal .env loader for Zoho OAuth helper scripts (no pydantic / dotenv package)."""
from __future__ import annotations

import os
import re
from pathlib import Path


def _parse_value(raw: str) -> str:
    """
    Strip quotes; for unquoted values, drop inline comments (whitespace + # ... end-of-line).
    So ZOHO_CLIENT_ID=id  # comment does not poison the id with '# comment'.
    """
    s = raw.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return re.sub(r"\s+#.*$", "", s).strip()


def load_dotenv(path: Path) -> None:
    """
    Set os.environ keys from KEY=VALUE lines. Does not override existing environment variables.
    """
    if not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if not key:
            continue
        val = _parse_value(val)
        if key not in os.environ:
            os.environ[key] = val
