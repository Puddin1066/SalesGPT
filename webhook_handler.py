"""
Webhook Handler for Smartlead Reply Events.

Catches reply events from Smartlead and processes them through SalesGPT.
"""
import os
import json
import hmac
import hashlib
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import asyncio
from datetime import datetime

import stripe

from salesgpt.config import get_settings
from salesgpt.container import ServiceContainer
from main_agent import ASSCHOrchestrator

# Load settings
settings = get_settings()

# Initialize container and orchestrator
container = ServiceContainer(settings)
orchestrator = container.orchestrator

# Configure Stripe (optional)
if settings.stripe_api_key:
    stripe.api_key = settings.stripe_api_key

# Initialize FastAPI app
app = FastAPI(title="ASSCH Webhook Handler")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Pydantic models for request validation
class SmartleadWebhookPayload(BaseModel):
    """Webhook payload model for Smartlead."""
    event: str
    thread_id: str
    sender_email: EmailStr
    sender_name: str = ""
    body: str


class StripeWebhookAck(BaseModel):
    """Simple response model for Stripe webhook acknowledgements."""
    status: str


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify HMAC signature for webhook security.
    
    Args:
        payload: Raw request body bytes
        signature: Signature from X-Smartlead-Signature header
        secret: Secret key for verification
        
    Returns:
        True if signature is valid, False otherwise
    """
    if not signature or not secret:
        return False
    
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)


@app.post("/webhook/smartlead")
@limiter.limit("100/minute")
async def handle_smartlead_webhook(request: Request):
    """
    Handle Smartlead webhook events with signature verification and rate limiting.
    
    Expected payload:
    {
        "event": "email_replied",
        "thread_id": "...",
        "sender_email": "...",
        "sender_name": "...",
        "body": "..."
    }
    """
    try:
        # Get raw body for signature verification
        body_bytes = await request.body()
        
        # Verify webhook signature
        signature = request.headers.get("X-Smartlead-Signature")
        if signature and not verify_webhook_signature(body_bytes, signature, settings.webhook_secret_key):
            raise HTTPException(
                status_code=401,
                detail="Invalid webhook signature"
            )
        
        # Parse and validate payload
        try:
            payload_dict = json.loads(body_bytes.decode())
            payload = SmartleadWebhookPayload(**payload_dict)
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid payload: {str(e)}"
            )
        
        # Parse and validate payload
        try:
            payload_dict = json.loads(body_bytes.decode())
            payload = SmartleadWebhookPayload(**payload_dict)
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid payload: {str(e)}"
            )
        
        # Validate event type
        if payload.event != "email_replied":
            return JSONResponse(
                {"status": "ignored", "reason": f"Event type {payload.event} not handled"}
            )
        
        # Process reply asynchronously
        await orchestrator.handle_reply(
            thread_id=payload.thread_id,
            sender_email=payload.sender_email,
            sender_name=payload.sender_name,
            email_body=payload.body
        )
        
        # Track reply metrics for analytics
        lead_state = orchestrator.state.get_lead_state(payload.sender_email)
        
        if lead_state:
            # Get intent from SalesGPT classification
            intent = orchestrator.salesgpt.classify_intent(
                payload.body,
                orchestrator.state.get_conversation_history(payload.thread_id)
            )
            
            # Update lead state with reply tracking
            orchestrator.state.update_lead_state(
                payload.sender_email,
                {
                    "reply_received_at": datetime.now(),
                    "reply_intent": intent,
                    "status": "replied"
                }
            )
            
            # Track booking if intent is interested
            if intent == "interested":
                orchestrator.state.update_lead_state(
                    payload.sender_email,
                    {
                        "booked_at": datetime.now(),
                        "status": "booked"
                    }
                )
        
        return JSONResponse({"status": "success", "message": "Reply processed"})
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Webhook error: {e}")
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )


@app.post("/webhook/stripe", response_model=StripeWebhookAck)
@limiter.limit("200/minute")
async def handle_stripe_webhook(request: Request):
    """
    Handle Stripe webhooks to record paid conversion events (paid Pro subscriptions).
    
    Success criterion (locked):
    - event.type == invoice.paid
    - invoice lines contain settings.stripe_pro_price_id_live
    - Stripe Customer email matches lead.email
    """
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=500, detail="Stripe webhook secret not configured")
    if not settings.stripe_api_key:
        raise HTTPException(status_code=500, detail="Stripe API key not configured")
    if not settings.stripe_pro_price_id_live:
        raise HTTPException(status_code=500, detail="STRIPE_PRO_PRICE_ID_LIVE not configured")

    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.stripe_webhook_secret,
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Stripe payload: {type(e).__name__}")

    # Only care about invoice.paid for subscriptions
    if event.get("type") != "invoice.paid":
        return StripeWebhookAck(status="ignored")

    invoice = event.get("data", {}).get("object", {})
    if not invoice:
        return StripeWebhookAck(status="ignored")

    # Check if the paid invoice includes the Pro price
    pro_price_id = settings.stripe_pro_price_id_live
    lines = (invoice.get("lines") or {}).get("data") or []
    has_pro_price = False
    for line in lines:
        price = ((line.get("price") or {}) if isinstance(line, dict) else {}) or {}
        if price.get("id") == pro_price_id:
            has_pro_price = True
            break

    if not has_pro_price:
        return StripeWebhookAck(status="ignored")

    # Map Stripe customer to lead via customer email (ground truth)
    customer_id = invoice.get("customer")
    if not customer_id:
        return StripeWebhookAck(status="ignored")

    try:
        customer = stripe.Customer.retrieve(customer_id)
        customer_email = (customer.get("email") or "").strip().lower()
    except Exception:
        # Don't fail the webhook; just ignore if we can't resolve customer email
        return StripeWebhookAck(status="ignored")

    if not customer_email:
        return StripeWebhookAck(status="ignored")

    # Update lead state in SalesGPT DB
    lead_state = orchestrator.state.get_lead_state(customer_email)
    if not lead_state:
        # Lead not tracked in our system (could be organic). Ignore for A/B reward.
        return StripeWebhookAck(status="ignored")

    paid_amount = None
    try:
        # Stripe amounts are in cents
        amount_paid = invoice.get("amount_paid")
        if isinstance(amount_paid, (int, float)):
            paid_amount = float(amount_paid) / 100.0
    except Exception:
        paid_amount = None

    orchestrator.state.update_lead_state(
        customer_email,
        {
            "paid_pro_at": datetime.utcnow(),
            "paid_pro_price_id": pro_price_id,
            "paid_pro_invoice_id": invoice.get("id"),
            "paid_pro_amount": paid_amount,
            "status": "paid_pro",
        },
    )

    return StripeWebhookAck(status="ok")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    port = settings.webhook_port
    uvicorn.run(app, host="0.0.0.0", port=port)
