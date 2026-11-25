
import os
import json
import base64
import urllib.request
import urllib.error
import urllib.parse
import re
from typing import Any

from sqlalchemy.orm import Session

from app.plugins.base_plugin import BasePlugin
from app.database.models import JiraTicket


class JiraPlugin(BasePlugin):

    def __init__(self, db: Session):
        super().__init__("jira")
        self.db = db

    def _get_configuration(self):
        base_url = os.getenv("JIRA_BASE_URL", "").strip().rstrip("/")
        email = os.getenv("JIRA_EMAIL", "").strip()
        api_token = os.getenv("JIRA_API_TOKEN", "").strip()
        project_key = os.getenv("JIRA_PROJECT_KEY", "").strip()

        missing = [
            key
            for key, value in {
                "JIRA_BASE_URL": base_url,
                "JIRA_EMAIL": email,
                "JIRA_API_TOKEN": api_token,
                "JIRA_PROJECT_KEY": project_key,
            }.items()
            if not value
        ]

        if missing:
            raise ValueError(
                "Missing Jira configuration: " + ", ".join(missing)
            )

        if not base_url.startswith(("https://", "http://")):
            raise ValueError(
                "JIRA_BASE_URL must be a valid HTTP or HTTPS URL."
            )

        credentials = f"{email}:{api_token}"
        encoded_credentials = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("utf-8")

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic {encoded_credentials}",
        }

        return base_url, project_key, headers

    @staticmethod
    def _normalize_text(value: str) -> str:
        """Normalize whitespace before comparing Jira descriptions."""

        return re.sub(r"\s+", " ", str(value or "")).strip().casefold()

    @staticmethod
    def _extract_adf_text(value: Any) -> str:
        """Extract readable text from Jira's Atlassian Document Format."""

        parts = []

        def walk(node):
            if isinstance(node, dict):
                if node.get("type") == "text":
                    parts.append(node.get("text", ""))

                for child in node.get("content", []):
                    walk(child)

            elif isinstance(node, list):
                for child in node:
                    walk(child)

        walk(value)
        return " ".join(parts)

    @staticmethod
    def _escape_jql(value: str) -> str:
        """Escape a value used inside a Jira JQL quoted string."""

        return value.replace("\\", "\\\\").replace('"', '\\"')

    def _find_existing_jira_issue(
        self,
        base_url: str,
        project_key: str,
        title: str,
        description: str,
        headers: dict,
    ):
        """
        Search Jira for an issue with the same title and description.

        Search errors are raised instead of silently creating a ticket.
        This prevents duplicate creation when Jira cannot be checked.
        """

        escaped_project = self._escape_jql(project_key)
        escaped_title = self._escape_jql(title)

        jql = (
            f'project = "{escaped_project}" '
            f'AND summary = "{escaped_title}" '
            f"ORDER BY created DESC"
        )

        next_page_token = None

        for _ in range(5):
            params = {
                "jql": jql,
                "maxResults": 100,
                "fields": "summary,description,status",
            }

            if next_page_token:
                params["nextPageToken"] = next_page_token

            query_string = urllib.parse.urlencode(params)

            request = urllib.request.Request(
                url=f"{base_url}/rest/api/3/search/jql?{query_string}",
                headers=headers,
                method="GET",
            )

            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.loads(
                    response.read().decode("utf-8")
                )

            for issue in result.get("issues", []):
                fields = issue.get("fields", {})

                existing_title = fields.get("summary", "")
                existing_description = self._extract_adf_text(
                    fields.get("description")
                )

                if (
                    self._normalize_text(existing_title)
                    == self._normalize_text(title)
                    and self._normalize_text(existing_description)
                    == self._normalize_text(description)
                ):
                    status_data = fields.get("status") or {}

                    return {
                        "jira_issue_key": issue.get("key"),
                        "jira_issue_id": issue.get("id"),
                        "status": status_data.get("name", "Existing"),
                    }

            next_page_token = result.get("nextPageToken")

            if not next_page_token:
                break

        return None

    def _find_existing_local_ticket(self, title: str, description: str):
        """Find an identical ticket already stored in AgentFlow."""

        return (
            self.db.query(JiraTicket)
            .filter(
                JiraTicket.title == title[:200],
                JiraTicket.description == description,
                JiraTicket.jira_issue_key.isnot(None),
            )
            .order_by(JiraTicket.id.desc())
            .first()
        )

    def _save_local_ticket(
        self,
        title: str,
        description: str,
        jira_issue_key: str,
        jira_issue_url: str,
        status: str,
    ):
        """Save a Jira issue locally if it is not already recorded."""

        existing = (
            self.db.query(JiraTicket)
            .filter(
                JiraTicket.jira_issue_key == jira_issue_key
            )
            .first()
        )

        if existing:
            return existing

        ticket = JiraTicket(
            title=title[:200],
            description=description,
            status=status or "Open",
            jira_issue_key=jira_issue_key,
            jira_issue_url=jira_issue_url,
        )

        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)

        return ticket

    def _duplicate_response(
        self,
        title: str,
        jira_issue_key: str,
        jira_issue_id: str | None,
        jira_issue_url: str,
        status: str,
        ticket_id: int | None = None,
    ):
        return {
            "success": True,
            "duplicate": True,
            "plugin": self.name,
            "ticket_id": ticket_id,
            "jira_issue_id": jira_issue_id,
            "jira_issue_key": jira_issue_key,
            "jira_issue_url": jira_issue_url,
            "title": title,
            "status": status,
            "message": (
                "Matching Jira issue already exists. "
                "No new ticket was created."
            ),
        }

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

        try:
            base_url, project_key, headers = self._get_configuration()

            # Check Jira itself before creating a new issue.
            existing_issue = self._find_existing_jira_issue(
                base_url=base_url,
                project_key=project_key,
                title=title,
                description=description,
                headers=headers,
            )

            if existing_issue:
                issue_key = existing_issue["jira_issue_key"]
                issue_url = f"{base_url}/browse/{issue_key}"

                ticket = self._save_local_ticket(
                    title=title,
                    description=description,
                    jira_issue_key=issue_key,
                    jira_issue_url=issue_url,
                    status=existing_issue["status"],
                )

                return self._duplicate_response(
                    title=title,
                    jira_issue_key=issue_key,
                    jira_issue_id=existing_issue.get("jira_issue_id"),
                    jira_issue_url=issue_url,
                    status=existing_issue["status"],
                    ticket_id=ticket.id,
                )

            # Check the local database as an additional safeguard.
            local_ticket = self._find_existing_local_ticket(
                title,
                description,
            )

            if local_ticket:
                return self._duplicate_response(
                    title=title,
                    jira_issue_key=local_ticket.jira_issue_key,
                    jira_issue_id=None,
                    jira_issue_url=local_ticket.jira_issue_url,
                    status=local_ticket.status or "Existing",
                    ticket_id=local_ticket.id,
                )

            # No duplicate found: create the actual Jira issue.
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
                headers=headers,
                method="POST",
            )

            with urllib.request.urlopen(request, timeout=30) as response:
                response_data = json.loads(
                    response.read().decode("utf-8")
                )

            jira_issue_key = response_data.get("key")
            jira_issue_id = response_data.get("id")

            if not jira_issue_key:
                return {
                    "success": False,
                    "duplicate": False,
                    "plugin": self.name,
                    "message": "Jira API did not return an issue key.",
                }

            jira_issue_url = f"{base_url}/browse/{jira_issue_key}"

            ticket = self._save_local_ticket(
                title=title,
                description=description,
                jira_issue_key=jira_issue_key,
                jira_issue_url=jira_issue_url,
                status="Open",
            )

            return {
                "success": True,
                "duplicate": False,
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
                "utf-8",
                errors="replace",
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
                "duplicate": False,
                "plugin": self.name,
                "http_status": error.code,
                "message": f"Jira API error: {message}",
            }

        except urllib.error.URLError as error:
            self.db.rollback()

            return {
                "success": False,
                "duplicate": False,
                "plugin": self.name,
                "message": f"Could not connect to Jira: {error.reason}",
            }

        except Exception as error:
            self.db.rollback()

            return {
                "success": False,
                "duplicate": False,
                "plugin": self.name,
                "message": f"Jira integration failed: {str(error)}",
            }
