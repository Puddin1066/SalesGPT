"""
Webhook Handler for Smartlead Reply Events.

Catches reply events from Smartlead and processes them through SalesGPT.
"""
import os
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import asyncio
from dotenv import load_dotenv

from main_agent import ASSCHOrchestrator

load_dotenv(".env.local")

app = FastAPI(title="ASSCH Webhook Handler")

# Initialize orchestrator
orchestrator = ASSCHOrchestrator()


@app.post("/webhook/smartlead")
async def handle_smartlead_webhook(request: Request):
    """
    Handle Smartlead webhook events.
    
    Expected payload:
    {
        "event": "email_replied",
        "thread_id": "...",
        "sender_email": "...",
        "sender_name": "...",
        "body": "...",
        ...
    }
    """
    try:
        payload = await request.json()
        event_type = payload.get("event")
        
        if event_type != "email_replied":
            return JSONResponse(
                {"status": "ignored", "reason": f"Event type {event_type} not handled"}
            )
        
        thread_id = payload.get("thread_id")
        sender_email = payload.get("sender_email")
        sender_name = payload.get("sender_name", "")
        email_body = payload.get("body", "")
        
        if not all([thread_id, sender_email, email_body]):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: thread_id, sender_email, body"
            )
        
        # Process reply asynchronously
        await orchestrator.handle_reply(
            thread_id=thread_id,
            sender_email=sender_email,
            sender_name=sender_name,
            email_body=email_body
        )
        
        return JSONResponse({"status": "success", "message": "Reply processed"})
        
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
    
    port = int(os.getenv("WEBHOOK_PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
