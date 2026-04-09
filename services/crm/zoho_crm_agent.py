"""
Zoho CRM API agent — Contacts and Deals (HubSpotAgent-shaped surface).

Uses OAuth refresh token. API base must match your Zoho data center (com / eu / in / au / ca / jp).

Record IDs are returned as strings; the rest of the app may store them in ``hubspot_contact_id`` /
``hubspot_deal_id`` metadata keys for compatibility — values are Zoho IDs when this agent is used.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Literal, Optional

import requests

from services.zoho.oauth_helper import refresh_zoho_access_token


class ZohoCRMAgent:
    """Zoho CRM v6 wrapper aligned with common HubSpotAgent call patterns."""

    PIPELINE_STAGES = {
        "idle": "idle",
        "engaged": "engaged",
        "booked": "booked",
        "closed": "closed",
    }

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        accounts_domain: Optional[str] = None,
        crm_api_base: Optional[str] = None,
        deal_stage_idle: Optional[str] = None,
        deal_stage_engaged: Optional[str] = None,
        deal_stage_booked: Optional[str] = None,
        deal_stage_closed: Optional[str] = None,
        fallback_contact_field: Optional[str] = None,
    ):
        self.client_id = client_id or os.getenv("ZOHO_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("ZOHO_CLIENT_SECRET", "")
        self.refresh_token = refresh_token or os.getenv("ZOHO_REFRESH_TOKEN", "")
        self.accounts_domain = (
            accounts_domain or os.getenv("ZOHO_ACCOUNTS_DOMAIN", "https://accounts.zoho.com")
        ).rstrip("/")
        self.crm_api_base = (
            crm_api_base or os.getenv("ZOHO_CRM_API_BASE", "https://www.zohoapis.com/crm/v6")
        ).rstrip("/")

        self._stage_map = {
            "idle": deal_stage_idle or os.getenv("ZOHO_DEAL_STAGE_IDLE", "Qualification"),
            "engaged": deal_stage_engaged or os.getenv("ZOHO_DEAL_STAGE_ENGAGED", "Qualification"),
            "booked": deal_stage_booked or os.getenv("ZOHO_DEAL_STAGE_BOOKED", "Closed Won"),
            "closed": deal_stage_closed or os.getenv("ZOHO_DEAL_STAGE_CLOSED", "Closed Lost"),
        }
        self._fallback_contact_field = fallback_contact_field or os.getenv(
            "ZOHO_CONTACT_STAGE_FIELD", "Lead_Status"
        )

        use_mock = os.getenv("USE_MOCK_APIS", "false").lower() == "true"
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            if use_mock:
                self.access_token = "mock_zoho_token"
                self.refresh_token = "mock_refresh"
                print("⚠️  Zoho CRM: mock mode (no real OAuth credentials)")
            else:
                raise ValueError(
                    "Zoho CRM requires ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, and ZOHO_REFRESH_TOKEN"
                )
        else:
            self.access_token = ""
            if not self._refresh_access_token():
                raise ValueError("Zoho CRM: could not obtain access_token (check OAuth app and refresh token scopes).")
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
        # Token response includes the correct CRM API host per org/DC (US, EU, IN, …).
        api_domain = (data.get("api_domain") or "").strip().rstrip("/")
        if api_domain:
            self.crm_api_base = f"{api_domain}/crm/v6"
        return True

    def _update_headers(self) -> None:
        self.headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        response = requests.request(method, url, headers=self.headers, timeout=60, **kwargs)
        if response.status_code == 401 and not self.access_token.startswith("mock"):
            if self._refresh_access_token():
                self._update_headers()
                response = requests.request(method, url, headers=self.headers, timeout=60, **kwargs)
        return response

    def _coerce_id(self, record: Dict[str, Any]) -> Optional[str]:
        details = record.get("details") if isinstance(record, dict) else None
        if isinstance(details, dict) and details.get("id"):
            return str(details["id"])
        if record.get("id"):
            return str(record["id"])
        return None

    @staticmethod
    def _data_response_first_id(data: Any) -> Optional[str]:
        if not isinstance(data, dict):
            return None
        rows = data.get("data")
        if not rows or not isinstance(rows, list):
            return None
        first = rows[0]
        return ZohoCRMAgent._coerce_id(first)  # type: ignore[arg-type]

    def create_contact(
        self,
        email: str,
        first_name: str,
        last_name: str,
        company: Optional[str] = None,
        website: Optional[str] = None,
        phone: Optional[str] = None,
        title: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        postal_code: Optional[str] = None,
        additional_properties: Optional[Dict] = None,
    ) -> Optional[str]:
        row: Dict[str, Any] = {
            "Email": email,
            "First_Name": first_name or "-",
            "Last_Name": last_name or "-",
        }
        if company:
            row["Account_Name"] = company
        if website:
            row["Website"] = website
        if phone:
            row["Phone"] = phone
        if title:
            row["Title"] = title
        if linkedin_url:
            row["Description"] = (row.get("Description") or "") + f"\nLinkedIn: {linkedin_url}"
        if city:
            row["Mailing_City"] = city
        if state:
            row["Mailing_State"] = state
        if country:
            row["Mailing_Country"] = country
        if postal_code:
            row["Mailing_Zip"] = postal_code
        if additional_properties:
            for k, v in additional_properties.items():
                if v is not None and v != "":
                    row[k] = v

        if self.access_token.startswith("mock"):
            return f"mock_zoho_contact_{abs(hash(email)) % 10_000_000}"

        try:
            response = self._request(
                "POST",
                f"{self.crm_api_base}/Contacts",
                json={"data": [row]},
            )
            response.raise_for_status()
            return self._data_response_first_id(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Zoho CRM error creating contact: {e}")
            return None

    def get_contact_by_email(self, email: str) -> Optional[Dict]:
        if self.access_token.startswith("mock"):
            return None
        criteria = f"(Email:equals:{email})"
        try:
            response = self._request(
                "GET",
                f"{self.crm_api_base}/Contacts/search",
                params={"criteria": criteria},
            )
            if response.status_code != 200:
                return None
            data = response.json()
            rows = data.get("data") or []
            if not rows:
                return None
            return rows[0]
        except requests.exceptions.RequestException:
            return None

    def update_contact_properties(self, contact_id: str, properties: Dict[str, str]) -> bool:
        if self.access_token.startswith("mock"):
            return True
        row = {k: v for k, v in properties.items() if v is not None}
        if not row:
            return True
        try:
            response = self._request(
                "PUT",
                f"{self.crm_api_base}/Contacts/{contact_id}",
                json={"data": [row]},
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Zoho CRM error updating contact: {e}")
            return False

    def _search_deals_for_contact(self, contact_id: str) -> List[Dict[str, Any]]:
        if self.access_token.startswith("mock"):
            return []
        criteria = f"(Contact_Name.id:equals:{contact_id})"
        try:
            response = self._request(
                "GET",
                f"{self.crm_api_base}/Deals/search",
                params={"criteria": criteria},
            )
            if response.status_code != 200:
                return []
            data = response.json()
            return data.get("data") or []
        except requests.exceptions.RequestException:
            return []

    def update_pipeline_stage(
        self,
        contact_id: str,
        stage: Literal["idle", "engaged", "booked", "closed"],
    ) -> bool:
        if stage not in self.PIPELINE_STAGES:
            raise ValueError(f"Invalid stage: {stage}")
        zoho_stage = self._stage_map.get(stage, self._stage_map["idle"])

        if self.access_token.startswith("mock"):
            return True

        deals = self._search_deals_for_contact(contact_id)
        if deals:
            deal_id = deals[0].get("id")
            if not deal_id:
                return False
            try:
                response = self._request(
                    "PUT",
                    f"{self.crm_api_base}/Deals/{deal_id}",
                    json={"data": [{"Stage": zoho_stage}]},
                )
                response.raise_for_status()
                return True
            except requests.exceptions.RequestException as e:
                print(f"Zoho CRM error updating deal stage: {e}")
                return False

        return self.update_contact_properties(
            contact_id, {self._fallback_contact_field: zoho_stage}
        )

    def create_deal(
        self,
        contact_id: str,
        deal_name: str,
        amount: Optional[float] = None,
        stage: str = "idle",
    ) -> Optional[str]:
        zoho_stage = self._stage_map.get(stage, self._stage_map["idle"])
        row: Dict[str, Any] = {
            "Deal_Name": deal_name,
            "Stage": zoho_stage,
            "Contact_Name": {"id": contact_id},
        }
        if amount is not None:
            row["Amount"] = amount

        if self.access_token.startswith("mock"):
            return f"mock_zoho_deal_{abs(hash(deal_name)) % 10_000_000}"

        try:
            response = self._request(
                "POST",
                f"{self.crm_api_base}/Deals",
                json={"data": [row]},
            )
            response.raise_for_status()
            return self._data_response_first_id(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Zoho CRM error creating deal: {e}")
            return None

    def create_or_update_contact(
        self,
        email: str,
        properties: Dict[str, str],
    ) -> Optional[str]:
        existing = self.get_contact_by_email(email)
        if existing and existing.get("id"):
            cid = str(existing["id"])
            zoho_props = self._hubspot_like_props_to_zoho(properties)
            if self.update_contact_properties(cid, zoho_props):
                return cid
            return cid
        return self.create_contact(
            email=email,
            first_name=properties.get("firstname", ""),
            last_name=properties.get("lastname", ""),
            company=properties.get("company"),
            website=properties.get("website"),
            phone=properties.get("phone"),
            title=properties.get("jobtitle"),
            linkedin_url=properties.get("linkedin"),
            city=properties.get("city"),
            state=properties.get("state"),
            country=properties.get("country"),
            postal_code=properties.get("zip"),
            additional_properties={
                k: v
                for k, v in properties.items()
                if k
                not in (
                    "email",
                    "firstname",
                    "lastname",
                    "company",
                    "website",
                    "phone",
                    "jobtitle",
                    "linkedin",
                    "city",
                    "state",
                    "country",
                    "zip",
                )
            },
        )

    @staticmethod
    def _hubspot_like_props_to_zoho(properties: Dict[str, str]) -> Dict[str, str]:
        """Map a few HubSpot-style keys to common Zoho API names (best-effort)."""
        mapping = {
            "firstname": "First_Name",
            "lastname": "Last_Name",
            "company": "Account_Name",
            "website": "Website",
            "phone": "Phone",
            "jobtitle": "Title",
            "city": "Mailing_City",
            "state": "Mailing_State",
            "country": "Mailing_Country",
            "zip": "Mailing_Zip",
        }
        out: Dict[str, str] = {}
        for k, v in properties.items():
            if v is None or v == "":
                continue
            out[mapping.get(k.lower(), k)] = v
        return out
