
import os
import smtplib
from typing import Any
from email.message import EmailMessage
from email.utils import parseaddr

from app.plugins.base_plugin import BasePlugin


class EmailPlugin(BasePlugin):
    """
    Sends real email notifications using Gmail SMTP.
    """

    def __init__(self):
        super().__init__("email")

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        recipient = str(data.get("recipient") or "").strip()
        subject = str(data.get("subject") or "").strip()
        message = str(data.get("message") or "").strip()

        # Validate required parameters
        if not recipient:
            raise ValueError("Email recipient is required.")

        if not subject:
            raise ValueError("Email subject is required.")

        if not message:
            raise ValueError("Email message is required.")

        # Basic recipient email validation
        parsed_name, parsed_email = parseaddr(recipient)

        if not parsed_email or "@" not in parsed_email:
            raise ValueError("Please provide a valid recipient email address.")

        # Read Gmail SMTP configuration
        smtp_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("EMAIL_PORT", "587"))
        sender = os.getenv("EMAIL_SENDER", "").strip()
        password = os.getenv("EMAIL_PASSWORD", "").replace(" ", "")

        if not sender:
            raise RuntimeError("EMAIL_SENDER is not configured.")

        if not password:
            raise RuntimeError("EMAIL_PASSWORD is not configured.")

        # Create email
        email = EmailMessage()
        email["From"] = sender
        email["To"] = recipient
        email["Subject"] = subject
        email.set_content(message)

        # Send real email through Gmail SMTP
        try:
            with smtplib.SMTP(
                smtp_host,
                smtp_port,
                timeout=30
            ) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                smtp.login(sender, password)
                smtp.send_message(email)

        except (smtplib.SMTPException, OSError) as exc:
            raise RuntimeError(
                f"Email delivery failed: {exc}"
            ) from exc

        return {
            "success": True,
            "plugin": self.name,
            "recipient": recipient,
            "subject": subject,
            "message": "Email sent successfully through Gmail SMTP."
        }
