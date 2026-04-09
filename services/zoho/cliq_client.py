"""
Minimal Zoho Cliq REST API client (OAuth access token from Zoho Accounts refresh).

Base URL: https://cliq.zoho.com (EU: https://cliq.zoho.eu, etc. via ZOHO_CLIQ_API_BASE).
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests


class ZohoCliqClient:
    def __init__(self, access_token: str, base_url: Optional[str] = None):
        self.base_url = (base_url or os.getenv("ZOHO_CLIQ_API_BASE") or "https://cliq.zoho.com").rstrip(
            "/"
        )
        self.access_token = access_token
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Zoho-oauthtoken {access_token}",
                "Accept": "application/json",
            }
        )

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
        return self._session.get(url, params=params, timeout=60)

    def post(self, path: str, json: Optional[Dict[str, Any]] = None) -> requests.Response:
        url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
        return self._session.post(url, json=json, timeout=60)
