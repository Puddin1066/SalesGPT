"""
Smartlead-shaped outbound adapter backed by Zoho Mail.

Campaigns/sequences are not Zoho Mail concepts: we store sequence templates in-process and send
the first step when leads are added. Follow-ups are your responsibility (Zoho CRM workflows,
scheduled jobs, or another tool).

When sending agent replies, pass ``recipient_email`` (main_agent passes the inbound sender).
"""
from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional

from services.outbound.zoho_mail_agent import ZohoMailAgent


class ZohoOutboundCompat:
    """Minimal compatibility surface for ``main_agent`` / webhooks."""

    def __init__(
        self,
        mail: ZohoMailAgent,
        from_address: str,
        from_display_name: str = "",
        send_delay_seconds: float = 0.0,
    ):
        self._mail = mail
        self._from_address = from_address
        self._from_display_name = from_display_name
        self._send_delay_seconds = send_delay_seconds
        self._sequences: List[Dict[str, Any]] = []
        self._campaign_id = 1

    def create_campaign(
        self,
        name: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        mailbox_ids: Optional[List[int]] = None,
        client_id: Optional[int] = None,
    ) -> Optional[int]:
        self._sequences.clear()
        if from_email:
            self._from_address = from_email
        if from_name:
            self._from_display_name = from_name
        return self._campaign_id

    def add_sequence(
        self,
        campaign_id: int,
        subject: str,
        body: str,
        delay_days: int = 0,
        seq_number: Optional[int] = None,
    ) -> Optional[int]:
        self._sequences.append(
            {
                "subject": subject,
                "body": body,
                "delay_days": delay_days,
            }
        )
        return len(self._sequences)

    @staticmethod
    def _render(template: str, ctx: Dict[str, str]) -> str:
        def repl(m: re.Match) -> str:
            key = m.group(1).strip()
            return ctx.get(key, m.group(0))

        return re.sub(r"\{\{\s*([^}]+?)\s*\}\}", repl, template)

    def _lead_to_ctx(self, lead: Dict[str, Any]) -> Dict[str, str]:
        custom = lead.get("custom_fields") or {}
        first = lead.get("first_name") or ""
        last = lead.get("last_name") or ""
        name = (first + " " + last).strip()
        ctx = {
            "first_name": first,
            "last_name": last,
            "name": name,
            "company_name": custom.get("company_name", "") or lead.get("company_name", ""),
            "location": custom.get("location", "") or lead.get("location", ""),
            "specialty": custom.get("specialty", "") or lead.get("specialty", ""),
            "website": custom.get("website", "") or lead.get("website", ""),
            "from_name": self._from_display_name or self._from_address.split("@")[0],
        }
        return ctx

    def add_leads_to_campaign(self, campaign_id: int, leads: List[Dict[str, Any]]) -> bool:
        if not leads:
            return False
        ok_count = 0
        primary = self._sequences[0] if self._sequences else None

        for lead in leads:
            to_email = lead.get("email")
            if not to_email:
                continue

            custom = lead.get("custom_fields") or {}
            subj = (custom.get("email_subject") or "").strip()
            body = (custom.get("email_body") or "").strip()
            ctx = self._lead_to_ctx(lead)

            if primary and not subj:
                subj = self._render(primary["subject"], ctx)
            if primary and not body:
                body = self._render(primary["body"], ctx)
            if not subj:
                subj = "Hello"
            if not body:
                body = "Hi — reaching out briefly."

            success = self._mail.send_message(
                from_address=self._from_address,
                to_address=to_email,
                subject=subj,
                content=body,
                mail_format="plaintext",
            )
            if success:
                ok_count += 1
            if self._send_delay_seconds > 0:
                time.sleep(self._send_delay_seconds)

        return ok_count > 0

    def send_reply(
        self,
        thread_id: str,
        body: str,
        subject: Optional[str] = None,
        recipient_email: Optional[str] = None,
    ) -> bool:
        if not recipient_email:
            print(
                "Zoho outbound: send_reply needs recipient_email (pass sender from webhook / handler)."
            )
            return False
        subj = subject or "Re:"
        return self._mail.send_message(
            from_address=self._from_address,
            to_address=recipient_email,
            subject=subj,
            content=body,
            mail_format="plaintext",
        )

    def get_mailboxes(self) -> List[Dict]:
        return [{"id": 1, "email": self._from_address}]

    def check_warmup_status(self, mailbox_id: int) -> Dict:
        return {"status": "not_applicable", "provider": "zoho_mail"}
