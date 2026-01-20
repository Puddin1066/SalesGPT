"""
Landing URL helpers for outbound campaigns.

Rules (deliverability-safe):
- Email 1: NO links.
- Email 2+: exactly one link, to the market landing page with UTMs.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode


MARKET_TO_PATH = {
    "medical": "/medical",
    "legal": "/legal",
    "realestate": "/real-estate",
    # Our landing-pages project calls this market "agencies" but the public path is marketing.
    "agencies": "/marketing",
}


def build_market_landing_url(
    base_url: str,
    market: str,
    utm_source: str,
    utm_campaign: str,
    utm_content: str | None = None,
    extra_params: dict | None = None,
) -> str:
    """
    Build landing URL for a given market, with UTMs.
    """
    base_url = base_url.rstrip("/")
    path = MARKET_TO_PATH.get(market)
    if not path:
        raise ValueError(f"Unknown market '{market}'")

    params = {
        "utm_source": utm_source,
        "utm_campaign": utm_campaign,
    }
    if utm_content:
        params["utm_content"] = utm_content
    if extra_params:
        params.update(extra_params)

    return f"{base_url}{path}?{urlencode(params)}"


