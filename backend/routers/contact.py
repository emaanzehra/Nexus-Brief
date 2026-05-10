"""NexusBrief — Contact Router"""

import logging
from fastapi import APIRouter
from core.schemas import ContactRequest

router = APIRouter(prefix="/contact", tags=["Contact"])
log = logging.getLogger("nexusbrief.contact")


@router.post("", status_code=200)
async def submit_contact(body: ContactRequest):
    """
    Accepts contact form submissions.
    In production: integrate with SendGrid / Mailgun / SES to send emails.
    Currently logs the submission and returns success.
    """
    log.info(
        "📬 Contact form | dept=%s | from=%s <%s> | subject=%s",
        body.department, body.name, body.email, body.subject,
    )
    # ── Production hook ──────────────────────────────────────────────────────
    # from services.email import send_contact_email
    # await send_contact_email(body)
    # ─────────────────────────────────────────────────────────────────────────
    return {"success": True, "message": "Message received. We'll respond within one business day."}
