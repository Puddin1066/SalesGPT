"""
Segmentation labeling helpers.

Goal:
- Deterministically map each lead to exactly one market (medical/legal/realestate/agencies)
- Derive persona from job title for better targeting

These are heuristics designed to be safe and adjustable.
"""

from __future__ import annotations


def infer_market(specialty: str, title: str | None = None, company_name: str | None = None) -> str:
    s = (specialty or "").lower()
    t = (title or "").lower()

    # Legal
    if any(k in s for k in ["law", "attorney", "legal", "litigation", "injury", "estate planning", "family law"]):
        return "legal"

    # Real estate
    if any(k in s for k in ["real estate", "realtor", "broker", "mortgage", "property"]):
        return "realestate"

    # Marketing agencies
    if any(k in s for k in ["marketing", "agency", "seo", "ppc", "growth"]):
        return "agencies"

    # Medical (default bucket for common clinical specialties)
    if any(k in s for k in ["medical", "health", "clinic", "dental", "dermatology", "orthopedic", "chiropractic"]):
        return "medical"

    # Fallback: use title hints if specialty is ambiguous
    if any(k in t for k in ["partner", "attorney", "lawyer"]):
        return "legal"
    if any(k in t for k in ["broker", "realtor"]):
        return "realestate"
    if any(k in t for k in ["marketing", "growth", "demand gen"]):
        return "agencies"

    # Last resort
    return "medical"


def infer_persona(title: str | None) -> str:
    """
    Collapse titles into a small set of personas for segmentation.
    """
    t = (title or "").lower()

    if any(word in t for word in ["owner", "founder", "ceo", "president", "principal"]):
        return "owner"
    if any(word in t for word in ["partner", "managing partner"]):
        return "partner"
    if any(word in t for word in ["director", "medical director"]):
        return "director"
    if any(word in t for word in ["practice manager", "office manager", "manager"]):
        return "manager"
    if any(word in t for word in ["marketing", "growth", "demand gen"]):
        return "marketing"

    return "other"


