"""
Workflow orchestration for SalesGPT.
"""
from workflows.background_queue_builder import BackgroundQueueBuilder

# ManualReviewWorkflow is just helper functions, not a class
# Import the functions directly
from workflows.manual_review_workflow import (
    load_pending_leads,
    approve_and_send,
    skip_lead,
    reject_lead,
    update_email_content
)

__all__ = [
    "BackgroundQueueBuilder",
    "load_pending_leads",
    "approve_and_send",
    "skip_lead",
    "reject_lead",
    "update_email_content"
]

