"""
Zoho Mail REST API — send messages using OAuth (Zoho-oauthtoken).

Requires scopes such as ZohoMail.messages.CREATE and ZohoMail.accounts.READ (to resolve accountId).
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests

from services.zoho.oauth_helper import refresh_zoho_access_token


class ZohoMailAgent:
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        accounts_domain: Optional[str] = None,
        mail_api_base: Optional[str] = None,
        account_id: Optional[str] = None,
    ):
        self.client_id = client_id or os.getenv("ZOHO_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("ZOHO_CLIENT_SECRET", "")
        self.refresh_token = refresh_token or os.getenv("ZOHO_REFRESH_TOKEN", "")
        self.accounts_domain = (
            accounts_domain or os.getenv("ZOHO_ACCOUNTS_DOMAIN", "https://accounts.zoho.com")
        ).rstrip("/")
        self.mail_api_base = (
            mail_api_base or os.getenv("ZOHO_MAIL_API_BASE", "https://mail.zoho.com")
        ).rstrip("/")
        self.account_id = (account_id or os.getenv("ZOHO_MAIL_ACCOUNT_ID") or "").strip() or None

        use_mock = os.getenv("USE_MOCK_APIS", "false").lower() == "true"
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            if use_mock:
                self.access_token = "mock_zoho_mail_token"
                print("⚠️  Zoho Mail: mock mode (no real OAuth credentials)")
            else:
                raise ValueError(
                    "Zoho Mail requires ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, and ZOHO_REFRESH_TOKEN"
                )
        else:
            self.access_token = ""
            if not self._refresh_access_token():
                raise ValueError("Zoho Mail: could not obtain access_token (check OAuth app and refresh token scopes).")
        self._update_headers()

    def _refresh_access_token(self) -> bool:
        data = refresh_zoho_access_token(
            self.client_id,
            self.client_secret,
            self.refresh_token,
            accounts_domain=self.accounts_domain,
        )
        if not data or not data.get("access_token"):
            return False
        self.access_token = data["access_token"]
        if data.get("refresh_token"):
            self.refresh_token = data["refresh_token"]
        return True

    def _update_headers(self) -> None:
        self.headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        response = requests.request(method, url, headers=self.headers, timeout=60, **kwargs)
        if response.status_code == 401 and not self.access_token.startswith("mock"):
            if self._refresh_access_token():
                self._update_headers()
                response = requests.request(method, url, headers=self.headers, timeout=60, **kwargs)
        return response

    def list_accounts(self) -> List[Dict[str, Any]]:
        """GET /api/accounts — used to resolve ``accountId`` when not configured."""
        if self.access_token.startswith("mock"):
            return [{"accountId": "mock_account", "primaryEmailAddress": "mock@example.com"}]
        try:
            response = self._request("GET", f"{self.mail_api_base}/api/accounts")
            response.raise_for_status()
            payload = response.json()
            data = payload.get("data")
            return data if isinstance(data, list) else []
        except requests.exceptions.RequestException as e:
            print(f"Zoho Mail list accounts failed: {e}")
            return []

    def resolve_account_id(self) -> Optional[str]:
        if self.account_id:
            return self.account_id
        accounts = self.list_accounts()
        if len(accounts) == 1:
            aid = accounts[0].get("accountId")
            if aid:
                self.account_id = str(aid)
                return self.account_id
        if len(accounts) > 1:
            print(
                "Zoho Mail: multiple accounts found; set ZOHO_MAIL_ACCOUNT_ID explicitly. "
                f"Candidates: {[a.get('accountId') for a in accounts]}"
            )
        return None

    def send_message(
        self,
        from_address: str,
        to_address: str,
        subject: str,
        content: str,
        mail_format: str = "plaintext",
    ) -> bool:
        """
        POST /api/accounts/{accountId}/messages

        See Zoho Mail API: Send an Email.
        """
        if self.access_token.startswith("mock"):
            print(f"[MOCK Zoho Mail] to={to_address} subject={subject[:40]!r}...")
            return True

        account_id = self.resolve_account_id()
        if not account_id:
            print("Zoho Mail: cannot send — no accountId (set ZOHO_MAIL_ACCOUNT_ID).")
            return False

        body: Dict[str, Any] = {
            "fromAddress": from_address,
            "toAddress": to_address,
            "subject": subject,
            "content": content,
            "mailFormat": mail_format,
        }

        try:
            response = self._request(
                "POST",
                f"{self.mail_api_base}/api/accounts/{account_id}/messages",
                json=body,
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Zoho Mail send failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    print(e.response.text[:500])
                except Exception:
                    pass
            return False
