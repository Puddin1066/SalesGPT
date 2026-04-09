"""
Zoho CRM API agent — Contacts and Deals (HubSpotAgent-shaped surface).

Uses OAuth refresh token. API base must match your Zoho data center (com / eu / in / au / ca / jp).

Record IDs are returned as strings; the rest of the app may store them in ``hubspot_contact_id`` /
``hubspot_deal_id`` metadata keys for compatibility — values are Zoho IDs when this agent is used.
"""
from __future__ import annotations

import os
import re
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

    def _crm_api_v9_base(self) -> str:
        """
        Campaign ↔ Lead / Contact related-list writes often require CRM API v9+ on newer orgs
        (v6 returns API_NOT_SUPPORTED / supported_version 9).
        """
        b = self.crm_api_base.rstrip("/")
        if re.search(r"/crm/v9$", b):
            return b
        b2 = re.sub(r"/crm/v\d+$", "/crm/v9", b)
        if b2 != b:
            return b2
        return f"{b}/crm/v9"

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        response = requests.request(method, url, headers=self.headers, timeout=60, **kwargs)
        if response.status_code == 401 and not self.access_token.startswith("mock"):
            if self._refresh_access_token():
                self._update_headers()
                response = requests.request(method, url, headers=self.headers, timeout=60, **kwargs)
        return response

    @staticmethod
    def _coerce_id(record: Any) -> Optional[str]:
        if not isinstance(record, dict):
            return None
        details = record.get("details")
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
        return ZohoCRMAgent._coerce_id(first)

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

    def add_note_to_record(
        self,
        module_api_name: str,
        record_id: str,
        title: str,
        content: str,
    ) -> bool:
        """Attach a Note to any module record (Contacts, Campaigns, Deals, …)."""
        if self.access_token.startswith("mock"):
            return True
        row: Dict[str, Any] = {
            "Parent_Id": {
                "module": {"api_name": module_api_name},
                "id": record_id,
            },
            "Note_Title": title[:255] if title else "Note",
            "Note_Content": content or "",
        }
        try:
            response = self._request(
                "POST",
                f"{self.crm_api_base}/Notes",
                json={"data": [row]},
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Zoho CRM error creating note: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    print(e.response.text[:500])
                except Exception:
                    pass
            return False

    def add_note_for_contact(self, contact_id: str, title: str, content: str) -> bool:
        """Attach a Note to a Contact."""
        return self.add_note_to_record("Contacts", contact_id, title, content)

    def create_campaign(
        self,
        campaign_name: str,
        *,
        campaign_type: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        description: Optional[str] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Create a Campaign record. Only Campaign_Name is universally required; Type/Status
        picklists vary by org — set ZOHO_CAMPAIGN_TYPE / ZOHO_CAMPAIGN_STATUS or pass args.
        Dates: YYYY-MM-DD if your org uses date fields for Start_Date / End_Date.
        """
        if self.access_token.startswith("mock"):
            return f"mock_campaign_{abs(hash(campaign_name)) % 10_000_000}"

        ctype = campaign_type or os.getenv("ZOHO_CAMPAIGN_TYPE", "Email")
        stat = status or os.getenv("ZOHO_CAMPAIGN_STATUS", "Planning")

        row: Dict[str, Any] = {"Campaign_Name": campaign_name}
        if ctype:
            row["Type"] = ctype
        if stat:
            row["Status"] = stat
        if start_date:
            row["Start_Date"] = start_date
        if end_date:
            row["End_Date"] = end_date
        if description:
            row["Description"] = description
        if extra_fields:
            for k, v in extra_fields.items():
                if v is not None and v != "":
                    row[k] = v

        def _post(payload: Dict[str, Any]) -> Optional[str]:
            try:
                response = self._request(
                    "POST",
                    f"{self.crm_api_base}/Campaigns",
                    json={"data": [payload]},
                )
                response.raise_for_status()
                return self._data_response_first_id(response.json())
            except requests.exceptions.RequestException as e:
                print(f"Zoho CRM error creating campaign: {e}")
                if hasattr(e, "response") and e.response is not None:
                    try:
                        print(e.response.text[:600])
                    except Exception:
                        pass
                return None

        cid = _post(row)
        if cid:
            return cid
        # Retry minimal row if picklists rejected
        return _post({"Campaign_Name": campaign_name})

    def create_lead(
        self,
        *,
        company: str,
        last_name: str = "-",
        first_name: str = "",
        email: Optional[str] = None,
        website: Optional[str] = None,
        lead_source: Optional[str] = None,
        description: Optional[str] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Create a Lead (use for prospects without a Contact email yet)."""
        if self.access_token.startswith("mock"):
            return f"mock_lead_{abs(hash(company)) % 10_000_000}"

        row: Dict[str, Any] = {
            "Company": company or "-",
            "Last_Name": last_name or "-",
            "First_Name": first_name or "",
        }
        if email:
            row["Email"] = email
        if website:
            row["Website"] = website
        if lead_source:
            row["Lead_Source"] = lead_source
        if description:
            row["Description"] = description
        if extra_fields:
            for k, v in extra_fields.items():
                if v is not None and v != "":
                    row[k] = v

        try:
            response = self._request(
                "POST",
                f"{self.crm_api_base}/Leads",
                json={"data": [row]},
            )
            response.raise_for_status()
            return self._data_response_first_id(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Zoho CRM error creating lead: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    print(e.response.text[:600])
                except Exception:
                    pass
            return None

    def relate_lead_to_campaign(self, campaign_id: str, lead_id: str) -> bool:
        """
        Link an existing Lead to a Campaign. Newer Zoho orgs reject v6 related-list POST
        (API_NOT_SUPPORTED / supported_version 9); we use CRM v9 and alternate shapes.
        """
        if self.access_token.startswith("mock"):
            return True
        base = self._crm_api_v9_base()
        last_text = ""

        url_camp = f"{base}/Campaigns/{campaign_id}/Leads"
        for body in (
            {"data": [{"Leads": {"id": lead_id}}]},
            {"data": [{"id": lead_id}]},
            {"data": [{"Lead_Name": {"id": lead_id}}]},
        ):
            try:
                r = self._request("POST", url_camp, json=body)
                last_text = r.text[:500]
                if r.ok:
                    return True
            except requests.exceptions.RequestException as e:
                last_text = str(e)
                continue

        # Lead-side associate (documented for v8+ on many orgs)
        url_lead = f"{base}/Leads/{lead_id}/Campaigns"
        for body in (
            {"data": [{"id": campaign_id}]},
            {"data": [{"Campaign_Name": {"id": campaign_id}}]},
        ):
            try:
                r = self._request("PUT", url_lead, json=body)
                last_text = r.text[:500]
                if r.ok:
                    return True
            except requests.exceptions.RequestException as e:
                last_text = str(e)
                continue

        print(
            f"Zoho CRM: could not relate lead {lead_id} to campaign {campaign_id}. Last response: {last_text}"
        )
        return False

    def relate_contact_to_campaign(self, campaign_id: str, contact_id: str) -> bool:
        """Link a Contact to a Campaign (CRM v9 + alternate related-list shapes)."""
        if self.access_token.startswith("mock"):
            return True
        base = self._crm_api_v9_base()
        last_text = ""

        url_camp = f"{base}/Campaigns/{campaign_id}/Contacts"
        for body in (
            {"data": [{"Contacts": {"id": contact_id}}]},
            {"data": [{"id": contact_id}]},
            {"data": [{"Contact_Name": {"id": contact_id}}]},
        ):
            try:
                r = self._request("POST", url_camp, json=body)
                last_text = r.text[:500]
                if r.ok:
                    return True
            except requests.exceptions.RequestException as e:
                last_text = str(e)
                continue

        url_ct = f"{base}/Contacts/{contact_id}/Campaigns"
        for body in (
            {"data": [{"id": campaign_id}]},
            {"data": [{"Campaign_Name": {"id": campaign_id}}]},
        ):
            try:
                r = self._request("PUT", url_ct, json=body)
                last_text = r.text[:500]
                if r.ok:
                    return True
            except requests.exceptions.RequestException as e:
                last_text = str(e)
                continue

        print(
            f"Zoho CRM: could not relate contact {contact_id} to campaign {campaign_id}. Last response: {last_text}"
        )
        return False

    def create_task_for_campaign(
        self,
        campaign_id: str,
        subject: str,
        due_date: str,
        description: str = "",
    ) -> bool:
        """Create a Task linked to a Campaign (What_Id + $se_module)."""
        if self.access_token.startswith("mock"):
            return True
        bases = (
            {
                "Subject": subject,
                "Due_Date": due_date,
                "What_Id": {"id": campaign_id},
                "$se_module": "Campaigns",
            },
            {
                "Subject": subject,
                "Due_Date": due_date,
                "What_Id": campaign_id,
                "$se_module": "Campaigns",
            },
        )
        last_err: Any = "unknown"
        for base in bases:
            row = dict(base)
            if description:
                row["Description"] = description
            try:
                response = self._request(
                    "POST",
                    f"{self.crm_api_base}/Tasks",
                    json={"data": [row]},
                )
                response.raise_for_status()
                return True
            except requests.exceptions.RequestException as e:
                last_err = e
                if hasattr(e, "response") and e.response is not None:
                    try:
                        last_err = e.response.text[:500]
                    except Exception:
                        pass
                continue
        print(f"Zoho CRM error creating campaign task (tried What_Id shapes): {last_err}")
        return False

    def create_task_for_contact(
        self,
        contact_id: str,
        subject: str,
        due_date: str,
        description: str = "",
    ) -> bool:
        """
        Create a Task linked to a Contact. due_date: YYYY-MM-DD (Zoho date field).
        """
        if self.access_token.startswith("mock"):
            return True
        row: Dict[str, Any] = {
            "Subject": subject,
            "Due_Date": due_date,
            "Who_Id": {"id": contact_id},
            "$se_module": "Contacts",
        }
        if description:
            row["Description"] = description
        try:
            response = self._request(
                "POST",
                f"{self.crm_api_base}/Tasks",
                json={"data": [row]},
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Zoho CRM error creating task: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    print(e.response.text[:500])
                except Exception:
                    pass
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
