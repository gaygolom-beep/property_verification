"""
Email notifications for verification status changes.

Entirely optional: if MAIL_SERVER isn't configured (see config.py), this
module never attempts to send anything -- it logs the notification instead
so the feature is visible/testable without needing real SMTP credentials.
A send failure (bad credentials, network issue, etc.) is caught and logged
too, so a broken mail setup never breaks the actual status-update flow.
"""
import logging

from flask import current_app
from flask_mail import Message

from extensions import mail

logger = logging.getLogger(__name__)

STATUS_SUBJECTS = {
    "In Review": "Your property is now under review",
    "Verified": "Your property has been verified",
    "Rejected": "Your property submission needs attention",
    "Pending": "Your property status was updated",
}


def send_status_change_email(prop, new_status, remarks=None):
    """
    prop: a Property instance (with .owner and .title)
    new_status: the new overall_status string
    remarks: optional admin remarks to include
    """
    owner_email = prop.owner.email if prop.owner else None
    if not owner_email:
        return

    subject = STATUS_SUBJECTS.get(new_status, "Your property status was updated")
    body = (
        f"Hi {prop.owner.full_name},\n\n"
        f"The verification status of your property \"{prop.title}\" has changed to: {new_status}.\n"
    )
    if remarks:
        body += f"\nRemarks from the reviewer:\n{remarks}\n"
    body += "\nYou can view the full details and audit history by logging into PropVerify.\n"

    if not current_app.config.get("MAIL_ENABLED"):
        logger.info("[mail disabled] Would have emailed %s: %s -- %s", owner_email, subject, new_status)
        return

    try:
        msg = Message(subject=subject, recipients=[owner_email], body=body)
        mail.send(msg)
    except Exception:  # noqa: BLE001 -- a notification failure must never break the status update
        logger.exception("Failed to send status-change email to %s", owner_email)
