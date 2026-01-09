"""
Unit tests for AB Test Manager.
"""
import pytest
from unittest.mock import MagicMock
from services.analytics.ab_test_manager import (
    ABTestManager,
    EmailVariant,
    SubjectVariant,
    BodyStructure,
    EvidenceLevel,
    CTAVariant
)


@pytest.fixture
def mock_state_manager():
    """Create mock state manager."""
    return MagicMock()


@pytest.fixture
def ab_manager(mock_state_manager):
    """Create AB test manager instance."""
    return ABTestManager(mock_state_manager)


def test_email_variant_to_code():
    """Test variant code generation."""
    variant = EmailVariant(
        subject_variant=SubjectVariant.COMPETITOR_MENTION,
        body_structure=BodyStructure.EVIDENCE_FIRST,
        evidence_level=EvidenceLevel.FULL,
        cta_variant=CTAVariant.DIRECT_BOOKING,
        personalization_level="high",
        email_length="medium"
    )
    
    code = variant.to_code()
    assert code == "competitor-evidence-full-direct-high-medium"


def test_assign_variant_central_route(ab_manager):
    """Test variant assignment for central route (high score)."""
    variant = ab_manager.assign_variant(
        "test@example.com",
        {"persuasion_route": "central", "score": 18}
    )
    
    assert variant.subject_variant in [SubjectVariant.COMPETITOR_MENTION, SubjectVariant.VALUE_PROP]
    assert variant.body_structure == BodyStructure.EVIDENCE_FIRST
    assert variant.evidence_level == EvidenceLevel.FULL
    assert variant.personalization_level == "high"


def test_assign_variant_peripheral_route(ab_manager):
    """Test variant assignment for peripheral route (low score)."""
    variant = ab_manager.assign_variant(
        "test@example.com",
        {"persuasion_route": "peripheral", "score": 8}
    )
    
    assert variant.subject_variant in [
        SubjectVariant.QUESTION,
        SubjectVariant.CURIOSITY,
        SubjectVariant.SOCIAL_PROOF
    ]
    assert variant.evidence_level in [EvidenceLevel.MINIMAL, EvidenceLevel.NONE]


def test_assign_variant_consistency(ab_manager):
    """Test that same email always gets same variant."""
    email = "test@example.com"
    characteristics = {"persuasion_route": "central", "score": 15}
    
    variant1 = ab_manager.assign_variant(email, characteristics)
    variant2 = ab_manager.assign_variant(email, characteristics)
    
    assert variant1.to_code() == variant2.to_code()


def test_generate_subject(ab_manager):
    """Test subject line generation."""
    lead = {
        "name": "John Doe",
        "company_name": "Test Clinic",
        "location": "New York, NY"
    }
    evidence = {
        "competitor_name": "Competitor Clinic",
        "referral_multiplier": 2.5,
        "gap_percentage": 15
    }
    
    subject = ab_manager._generate_subject(
        SubjectVariant.COMPETITOR_MENTION,
        lead,
        evidence
    )
    
    assert "Competitor Clinic" in subject
    assert "2.5x" in subject or "2.5" in subject


def test_get_cta_text(ab_manager):
    """Test CTA text generation."""
    lead = {"name": "John Doe"}
    
    cta = ab_manager._get_cta_text(CTAVariant.DIRECT_BOOKING, lead)
    assert "book" in cta.lower() or "call" in cta.lower()

