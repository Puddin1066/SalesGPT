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

from salesgpt.config import get_settings
from salesgpt.container import ServiceContainer
from main_agent import ASSCHOrchestrator

# Load settings
settings = get_settings()

# Initialize container and orchestrator
container = ServiceContainer(settings)
orchestrator = container.orchestrator

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
        from datetime import datetime
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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    port = settings.webhook_port
    uvicorn.run(app, host="0.0.0.0", port=port)
