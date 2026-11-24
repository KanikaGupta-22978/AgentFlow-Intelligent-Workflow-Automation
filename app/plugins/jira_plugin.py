
import os
import json
import base64
import urllib.request
import urllib.error
from typing import Any

from sqlalchemy.orm import Session

from app.plugins.base_plugin import BasePlugin
from app.database.models import JiraTicket


class JiraPlugin(BasePlugin):

    def __init__(self, db: Session):
        super().__init__("jira")
        self.db = db

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:

        title = str(data.get("title") or "").strip()
        description = str(data.get("description") or "").strip()
        alerts = data.get("alerts", [])

        if isinstance(alerts, list) and alerts:
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
                        f"Details: {first_alert.get('description', 'No additional details')}"
                    )

        if not title:
            title = "Operational Incident"

        base_url = os.getenv("JIRA_BASE_URL", "").strip().rstrip("/")
        email = os.getenv("JIRA_EMAIL", "").strip()
        api_token = os.getenv("JIRA_API_TOKEN", "").strip()
        project_key = os.getenv("JIRA_PROJECT_KEY", "").strip()

        missing = [
            key for key, value in {
                "JIRA_BASE_URL": base_url,
                "JIRA_EMAIL": email,
                "JIRA_API_TOKEN": api_token,
                "JIRA_PROJECT_KEY": project_key,
            }.items() if not value
        ]

        if missing:
            return {
                "success": False,
                "plugin": self.name,
                "message": "Missing Jira configuration: " + ", ".join(missing),
            }

        if not base_url.startswith(("https://", "http://")):
            return {
                "success": False,
                "plugin": self.name,
                "message": "JIRA_BASE_URL must be a valid HTTP or HTTPS URL.",
            }

        credentials = f"{email}:{api_token}"
        encoded_credentials = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("utf-8")

        description_content = []

        for paragraph in description.splitlines() or [""]:
            description_content.append({
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": paragraph}
                ] if paragraph else []
            })

        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": title,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": description_content,
                },
                "issuetype": {"name": "Task"},
            }
        }

        request = urllib.request.Request(
            url=f"{base_url}/rest/api/3/issue",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Basic {encoded_credentials}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                response_data = json.loads(
                    response.read().decode("utf-8")
                )

            jira_issue_key = response_data.get("key")
            jira_issue_id = response_data.get("id")

            if not jira_issue_key:
                return {
                    "success": False,
                    "plugin": self.name,
                    "message": "Jira API did not return an issue key.",
                }

            jira_issue_url = f"{base_url}/browse/{jira_issue_key}"

            ticket = JiraTicket(
                title=title[:200],
                description=description,
                status="Open",
                jira_issue_key=jira_issue_key,
                jira_issue_url=jira_issue_url,
            )

            self.db.add(ticket)
            self.db.commit()
            self.db.refresh(ticket)

            return {
                "success": True,
                "plugin": self.name,
                "ticket_id": ticket.id,
                "jira_issue_id": jira_issue_id,
                "jira_issue_key": jira_issue_key,
                "jira_issue_url": jira_issue_url,
                "title": title,
                "status": "Open",
                "message": "Real Jira issue created successfully.",
            }

        except urllib.error.HTTPError as error:
            error_body = error.read().decode(
                "utf-8", errors="replace"
            )
            self.db.rollback()

            try:
                details = json.loads(error_body)
                message = (
                    details.get("errorMessages")
                    or details.get("errors")
                    or error_body
                )
            except json.JSONDecodeError:
                message = error_body

            return {
                "success": False,
                "plugin": self.name,
                "http_status": error.code,
                "message": f"Jira API error: {message}",
            }

        except urllib.error.URLError as error:
            self.db.rollback()
            return {
                "success": False,
                "plugin": self.name,
                "message": f"Could not connect to Jira: {error.reason}",
            }

        except Exception as error:
            self.db.rollback()
            return {
                "success": False,
                "plugin": self.name,
                "message": f"Jira integration failed: {str(error)}",
            }
