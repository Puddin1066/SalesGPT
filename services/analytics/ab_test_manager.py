"""
Email A/B Test Manager.

Manages email variant assignment, generation, and tracking.
Tests: subject lines, body structure, evidence level, CTA variants.
"""
import hashlib
import random
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional


class SubjectVariant(Enum):
    COMPETITOR_MENTION = "competitor"
    QUESTION = "question"
    VALUE_PROP = "value"
    CURIOSITY = "curiosity"
    SOCIAL_PROOF = "social"
    URGENCY = "urgency"


class BodyStructure(Enum):
    EVIDENCE_FIRST = "evidence"
    PROBLEM_FIRST = "problem"
    STORY_FIRST = "story"
    QUESTION_FIRST = "question"


class EvidenceLevel(Enum):
    FULL = "full"
    MINIMAL = "minimal"
    NONE = "none"


class CTAVariant(Enum):
    DIRECT_BOOKING = "direct"
    SOFT_ASK = "soft"
    VALUE_FIRST = "value"
    TWO_STEP = "two_step"


@dataclass
class EmailVariant:
    """Email variant configuration."""
    subject_variant: SubjectVariant
    body_structure: BodyStructure
    evidence_level: EvidenceLevel
    cta_variant: CTAVariant
    personalization_level: str  # "high", "medium", "low"
    email_length: str  # "short", "medium", "long"
    
    def to_code(self) -> str:
        """Generate variant code (e.g., 'competitor-evidence-full-direct-high-medium')."""
        return f"{self.subject_variant.value}-{self.body_structure.value}-{self.evidence_level.value}-{self.cta_variant.value}-{self.personalization_level}-{self.email_length}"


class ABTestManager:
    """
    Manages A/B testing for email variants.
    
    Uses consistent hashing for reproducible variant assignment
    and tracks performance metrics per variant.
    """
    
    def __init__(self, state_manager):
        """
        Initialize AB Test Manager.
        
        Args:
            state_manager: StateManager instance for querying leads
        """
        self.state = state_manager
    
    def assign_variant(
        self,
        lead_email: str,
        lead_characteristics: Dict
    ) -> EmailVariant:
        """
        Assign email variant to lead based on characteristics.
        
        Uses consistent hashing on email for reproducibility.
        Smart assignment based on ELM route and lead score.
        
        Args:
            lead_email: Lead email address (used for consistent hashing)
            lead_characteristics: Dict with 'persuasion_route' and 'score'
            
        Returns:
            EmailVariant configuration
        """
        # Consistent hashing
        email_hash = int(hashlib.md5(lead_email.encode()).hexdigest()[:8], 16)
        random.seed(email_hash)
        
        # Get lead characteristics
        elm_route = lead_characteristics.get("persuasion_route", "peripheral")
        score = lead_characteristics.get("score", 0)
        
        # Smart variant assignment
        if elm_route == "central" and score >= 15:
            # High-quality leads: evidence-heavy, logical
            subject_variant = random.choice([
                SubjectVariant.COMPETITOR_MENTION,
                SubjectVariant.VALUE_PROP
            ])
            body_structure = BodyStructure.EVIDENCE_FIRST
            evidence_level = EvidenceLevel.FULL
            cta_variant = random.choice([CTAVariant.DIRECT_BOOKING, CTAVariant.VALUE_FIRST])
            personalization_level = "high"
            email_length = "medium"
        else:
            # Lower-quality leads: simpler, social proof
            subject_variant = random.choice([
                SubjectVariant.QUESTION,
                SubjectVariant.CURIOSITY,
                SubjectVariant.SOCIAL_PROOF
            ])
            body_structure = random.choice([
                BodyStructure.PROBLEM_FIRST,
                BodyStructure.QUESTION_FIRST
            ])
            evidence_level = random.choice([EvidenceLevel.MINIMAL, EvidenceLevel.NONE])
            cta_variant = random.choice([CTAVariant.SOFT_ASK, CTAVariant.TWO_STEP])
            personalization_level = random.choice(["medium", "low"])
            email_length = random.choice(["short", "medium"])
        
        return EmailVariant(
            subject_variant=subject_variant,
            body_structure=body_structure,
            evidence_level=evidence_level,
            cta_variant=cta_variant,
            personalization_level=personalization_level,
            email_length=email_length
        )
    
    def generate_email_from_variant(
        self,
        variant: EmailVariant,
        salesgpt_wrapper,
        lead: Dict,
        evidence: Optional[Dict] = None,
        competitor: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Generate email using SalesGPT with variant specifications.
        
        Args:
            variant: EmailVariant configuration
            salesgpt_wrapper: SalesGPTWrapper instance
            lead: Lead dictionary with name, company_name, location, specialty
            evidence: Optional competitive analysis evidence
            competitor: Optional competitor data
            
        Returns:
            Dictionary with 'subject', 'body', 'variant_code'
        """
        # Build competitive analysis if evidence provided
        competitive_analysis = {}
        if evidence:
            competitive_analysis = {
                "lead_score": evidence.get("lead_score", 0),
                "competitor_score": evidence.get("competitor_score", 0),
                "gap_percentage": evidence.get("gap_percentage", 0),
                "referral_multiplier": evidence.get("referral_multiplier", 1.0),
                "competitor_name": competitor.get("name", "local competitors") if competitor else "local competitors",
                "competitor_has_kg": competitor.get("has_kg", False) if competitor else False
            }
        
        # Generate subject line based on variant
        subject = self._generate_subject(
            variant.subject_variant,
            lead,
            competitive_analysis
        )
        
        # Generate body using SalesGPT
        if competitive_analysis and variant.evidence_level != EvidenceLevel.NONE:
            # Use existing method that includes competitor
            email_result = salesgpt_wrapper.generate_initial_email_with_competitor(
                lead_name=lead.get("name", ""),
                company_name=lead.get("company_name", ""),
                location=lead.get("location", ""),
                specialty=lead.get("specialty", ""),
                competitive_analysis=competitive_analysis
            )
            body = email_result.get("body", "")
        else:
            # Generate simpler email without competitor mention
            body = self._generate_simple_email(
                salesgpt_wrapper,
                lead,
                variant
            )
        
        # Adjust body based on variant specifications
        body = self._adjust_body_for_variant(body, variant, lead, competitive_analysis)
        
        # Adjust subject if needed
        subject = self._adjust_subject_for_variant(subject, variant, lead)
        
        return {
            "subject": subject,
            "body": body,
            "variant_code": variant.to_code()
        }
    
    def _generate_subject(
        self,
        variant: SubjectVariant,
        lead: Dict,
        evidence: Dict
    ) -> str:
        """Generate subject line based on variant."""
        first_name = lead.get("name", "").split()[0] if lead.get("name") else "Hi"
        competitor_name = evidence.get("competitor_name", "a competitor")
        multiplier = evidence.get("referral_multiplier", 2.0)
        gap = abs(evidence.get("gap_percentage", 15))
        company = lead.get("company_name", "your practice")
        
        subjects = {
            SubjectVariant.COMPETITOR_MENTION: f"{first_name}, {competitor_name} is getting {multiplier}x more ChatGPT referrals",
            SubjectVariant.QUESTION: f"Losing patients to {competitor_name}?",
            SubjectVariant.VALUE_PROP: f"{gap}% more visibility in ChatGPT searches",
            SubjectVariant.CURIOSITY: f"Quick question about {company}'s visibility",
            SubjectVariant.SOCIAL_PROOF: f"How 3 {lead.get('specialty', 'practices')} in {lead.get('location', 'your area')} doubled referrals",
            SubjectVariant.URGENCY: "The AI referral gap is widening"
        }
        
        return subjects.get(variant, subjects[SubjectVariant.CURIOSITY])
    
    def _generate_simple_email(
        self,
        salesgpt_wrapper,
        lead: Dict,
        variant: EmailVariant
    ) -> str:
        """Generate simple email without competitor evidence."""
        # Use a basic template for non-evidence emails
        name = lead.get("name", "").split()[0] if lead.get("name") else "there"
        company = lead.get("company_name", "")
        location = lead.get("location", "")
        
        if variant.body_structure == BodyStructure.PROBLEM_FIRST:
            return f"""Hi {name},

I noticed {company} in {location} and wanted to reach out about a common challenge many practices face.

Many healthcare providers are losing patient referrals they don't even know about because they're not visible in AI-powered searches.

Would you be open to a brief conversation about how to improve your practice's visibility?

Best regards"""
        
        elif variant.body_structure == BodyStructure.QUESTION_FIRST:
            return f"""Hi {name},

Quick question: How many new patients does {company} typically see each month?

I work with practices like yours to improve their patient acquisition through AI visibility optimization.

Would you be interested in learning more?

Best regards"""
        
        else:
            return f"""Hi {name},

I came across {company} and thought you might find this interesting.

Many practices in {location} are seeing significant improvements in patient referrals by optimizing their AI search visibility.

Would you be open to a brief call to discuss?

Best regards"""
    
    def _adjust_body_for_variant(
        self,
        body: str,
        variant: EmailVariant,
        lead: Dict,
        evidence: Dict
    ) -> str:
        """Adjust email body based on variant specifications."""
        # Adjust evidence level
        if variant.evidence_level == EvidenceLevel.MINIMAL and evidence:
            # Remove detailed numbers, keep competitor name only
            competitor = evidence.get("competitor_name", "competitors")
            # Simplify mentions of specific percentages/multipliers
            body = body.replace(f"{evidence.get('gap_percentage', 0)}%", "significantly")
            body = body.replace(f"{evidence.get('referral_multiplier', 0)}x", "more")
        
        elif variant.evidence_level == EvidenceLevel.NONE:
            # Remove all evidence mentions
            if evidence:
                competitor = evidence.get("competitor_name", "")
                if competitor:
                    body = body.replace(competitor, "competitors")
                # Remove specific numbers
                import re
                body = re.sub(r'\d+\.?\d*x', 'more', body)
                body = re.sub(r'\d+%', '', body)
        
        # Adjust CTA based on variant
        cta_text = self._get_cta_text(variant.cta_variant, lead)
        
        # Replace or append CTA
        if "Would you be open" in body or "Would you be interested" in body:
            # Replace existing CTA
            import re
            body = re.sub(r'Would you be (open|interested).*?', cta_text, body, flags=re.DOTALL)
        else:
            # Append CTA
            body = f"{body}\n\n{cta_text}"
        
        # Adjust length
        if variant.email_length == "short":
            # Truncate to ~50-75 words
            words = body.split()
            if len(words) > 75:
                body = " ".join(words[:75]) + "..."
        elif variant.email_length == "long":
            # Expand if too short
            words = body.split()
            if len(words) < 150:
                # Add more detail
                body = f"{body}\n\nI'd be happy to show you specific examples of how this has worked for similar practices in your area."
        
        return body
    
    def _get_cta_text(self, cta_variant: CTAVariant, lead: Dict) -> str:
        """Get call-to-action text based on variant."""
        name = lead.get("name", "").split()[0] if lead.get("name") else "you"
        
        ctas = {
            CTAVariant.DIRECT_BOOKING: f"Would you like to book a 15-minute call? I can show you exactly how this works.",
            CTAVariant.SOFT_ASK: f"Would you be open to a brief conversation?",
            CTAVariant.VALUE_FIRST: f"Want to see the full audit? I can share it on a quick call.",
            CTAVariant.TWO_STEP: f"Reply if interested, and I'll send you the details."
        }
        
        return ctas.get(cta_variant, ctas[CTAVariant.SOFT_ASK])
    
    def _adjust_subject_for_variant(
        self,
        subject: str,
        variant: EmailVariant,
        lead: Dict
    ) -> str:
        """Adjust subject line based on personalization level."""
        if variant.personalization_level == "low":
            # Remove name if present
            name = lead.get("name", "").split()[0] if lead.get("name") else ""
            if name and subject.startswith(f"{name},"):
                subject = subject.replace(f"{name}, ", "")
        
        return subject

