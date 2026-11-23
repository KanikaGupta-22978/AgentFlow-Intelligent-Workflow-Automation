
from typing import Any

from app.plugins.base_plugin import BasePlugin


class EmailPlugin(BasePlugin):
    """
    Mock Email plugin.
    Displays email notifications in the terminal.
    Does not send real emails.
    """

    def __init__(self):
        super().__init__("email")

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        recipient = data.get("recipient")
        subject = data.get("subject", "Workflow Notification")
        message = data.get("message", "")

        if not recipient:
            raise ValueError("Email recipient is required.")

        if not message:
            raise ValueError("Email message is required.")

        print("\n===== MOCK EMAIL NOTIFICATION =====")
        print("TO:", recipient)
        print("SUBJECT:", subject)
        print("MESSAGE:", message)
        print("===================================\n")

        return {
            "success": True,
            "plugin": self.name,
            "recipient": recipient,
            "subject": subject,
            "message": "Mock email notification generated successfully.",
        }
