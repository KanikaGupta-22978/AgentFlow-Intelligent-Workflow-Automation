
import os
import json
import urllib.request
import urllib.error
from typing import Any
from email.utils import parseaddr

from app.plugins.base_plugin import BasePlugin


class EmailPlugin(BasePlugin):
    """
    Sends real transactional emails using Brevo HTTPS API.
    """

    API_URL = "https://api.brevo.com/v3/smtp/email"

    def __init__(self):
        super().__init__("email")

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        recipient = str(data.get("recipient") or "").strip()
        subject = str(data.get("subject") or "").strip()
        message = str(data.get("message") or "").strip()

        if not recipient:
            raise ValueError("Email recipient is required.")

        _, parsed_email = parseaddr(recipient)

        if not parsed_email or "@" not in parsed_email:
            raise ValueError("Please provide a valid recipient email address.")

        if not subject:
            raise ValueError("Email subject is required.")

        if not message:
            raise ValueError("Email message is required.")

        api_key = os.getenv("BREVO_API_KEY", "").strip()
        sender = os.getenv("EMAIL_SENDER", "").strip()

        if not api_key:
            raise RuntimeError("BREVO_API_KEY is not configured.")

        if not sender:
            raise RuntimeError("EMAIL_SENDER is not configured.")

        payload = {
            "sender": {
                "name": "AgentFlow",
                "email": sender
            },
            "to": [
                {
                    "email": parsed_email
                }
            ],
            "subject": subject,
            "textContent": message
        }

        request = urllib.request.Request(
            self.API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "accept": "application/json",
                "api-key": api_key,
                "content-type": "application/json"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))

        except urllib.error.HTTPError as error:
            error_body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Brevo email delivery failed (HTTP {error.code}): "
                f"{error_body[:500]}"
            ) from error

        except urllib.error.URLError as error:
            raise RuntimeError(
                f"Could not connect to Brevo API: {error.reason}"
            ) from error

        return {
            "success": True,
            "plugin": self.name,
            "recipient": parsed_email,
            "subject": subject,
            "message": "Email accepted by Brevo for delivery.",
            "message_id": result.get("messageId")
        }
