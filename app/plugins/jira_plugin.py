
from typing import Any

from app.plugins.base_plugin import BasePlugin
from app.database.models import JiraTicket
from sqlalchemy.orm import Session


class JiraPlugin(BasePlugin):
    """
    Mock Jira plugin.
    Stores tickets in the local SQLite database.
    """

    def __init__(self, db: Session):
        super().__init__("jira")
        self.db = db

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        # Preserve support for directly supplied title and description.
        title = data.get("title")
        description = data.get("description", "")

        # If alerts are supplied, derive ticket details from them.
        alerts = data.get("alerts", [])

        if alerts and isinstance(alerts, list):
            first_alert = alerts[0]

            if isinstance(first_alert, dict):
                hostname = (
                    first_alert.get("hostname")
                    or first_alert.get("device")
                    or "Unknown Device"
                )

                intensity = first_alert.get("intensity", "Alert")

                if not title:
                    title = f"{intensity} Alert - {hostname}"

                if not description:
                    description = (
                        f"Operational alert for device: {hostname}\n"
                        f"Intensity: {intensity}\n"
                        f"Details: "
                        f"{first_alert.get('description', 'No additional details')}"
                    )

        if not title:
            title = "Operational Incident"

        ticket = JiraTicket(
            title=title,
            description=description,
            status="Open",
        )

        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)

        return {
            "success": True,
            "plugin": self.name,
            "ticket_id": ticket.id,
            "title": ticket.title,
            "status": ticket.status,
            "message": "Mock Jira ticket created successfully.",
        }
