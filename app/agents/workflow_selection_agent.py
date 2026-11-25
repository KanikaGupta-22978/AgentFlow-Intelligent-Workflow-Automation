
import re
from typing import Any

from app.services.data_service import get_available_zones


def select_workflow(user_instruction: str) -> str:
    """Select a predefined workflow from the user's instruction."""

    instruction = user_instruction.lower().strip()

    if not instruction:
        raise ValueError("Please provide a workflow instruction.")

    if any(word in instruction for word in ["ticket", "jira"]):
        return "WF002"

    if any(
        word in instruction
        for word in ["email", "notification", "send mail", "e-mail"]
    ):
        return "WF003"

    if any(word in instruction for word in ["alert", "alerts"]):
        return "WF001"

    if any(
        word in instruction
        for word in ["performance", "report"]
    ):
        return "WF004"

    raise ValueError(
        "Could not identify a matching workflow from the instruction."
    )


def extract_parameters(
    workflow_id: str,
    user_instruction: str,
) -> dict[str, Any]:
    """Extract supported parameters from natural-language instructions."""

    instruction = user_instruction.strip()
    parameters: dict[str, Any] = {}

    if workflow_id == "WF002":

        title_match = re.search(
            r"^\s*Title\s*:\s*(.+?)\s*$",
            instruction,
            re.IGNORECASE | re.MULTILINE,
        )

        description_match = re.search(
            r"^\s*Description\s*:\s*(.*?)(?=^\s*Project\s*:|\Z)",
            instruction,
            re.IGNORECASE | re.MULTILINE | re.DOTALL,
        )

        if title_match:
            parameters["title"] = title_match.group(1).strip()

        if description_match:
            parameters["description"] = (
                description_match.group(1).strip()
            )

        if not parameters.get("title"):
            natural_match = re.search(
                r"\b(?:create|raise|open)\s+"
                r"(?:a\s+)?(?:jira\s+)?ticket\s+"
                r"(?:for|about|regarding)\s+(.+)",
                instruction,
                re.IGNORECASE,
            )

            if natural_match:
                description = natural_match.group(1).strip()
                description = re.sub(
                    r"\s+and\s+(?:email|e-mail)\b.*$",
                    "",
                    description,
                    flags=re.IGNORECASE,
                ).strip(" .")

                parameters["description"] = description
                parameters["title"] = " ".join(
                    description.split()[:5]
                )

        if not parameters.get("description"):
            if parameters.get("title"):
                parameters["description"] = parameters["title"]

    elif workflow_id == "WF004":

        zones = get_available_zones()

        matched_zone = next(
            (
                zone for zone in zones
                if zone.casefold() in instruction.casefold()
            ),
            None,
        )

        if matched_zone:
            parameters["zone"] = matched_zone

        duration_match = re.search(
            r"\blast\s+(\d+(?:\.\d+)?)\s+hours?\b",
            instruction,
            re.IGNORECASE,
        )

        if duration_match:
            parameters["hours"] = float(duration_match.group(1))

    elif workflow_id == "WF003":

        email_match = re.search(
            r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}",
            instruction,
        )

        if email_match:
            parameters["recipient"] = email_match.group(0)

        subject_match = re.search(
            r"\bsubject\s*:\s*(.+?)(?=\s+message\s*:|$)",
            instruction,
            re.IGNORECASE,
        )

        if subject_match:
            parameters["subject"] = subject_match.group(1).strip()

        message_match = re.search(
            r"\bmessage\s*:\s*(.+)$",
            instruction,
            re.IGNORECASE,
        )

        if message_match:
            parameters["message"] = message_match.group(1).strip()

        if not parameters.get("subject"):
            if re.search(
                r"\b(performance|report)\b",
                instruction,
                re.IGNORECASE,
            ):
                parameters["subject"] = "Performance Summary Report"
            else:
                parameters["subject"] = "Operational Notification"

        if not parameters.get("message"):
            parameters["message"] = (
                "Please find the requested notification details."
            )

    return parameters


def validate_parameters(
    workflow_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """Validate mandatory and optional workflow parameters."""

    if not isinstance(parameters, dict):
        raise ValueError(
            "Workflow parameters must be a dictionary."
        )

    if workflow_id == "WF001":
        return {}

    elif workflow_id == "WF002":

        title = parameters.get("title")
        description = parameters.get("description")

        if not isinstance(title, str) or not title.strip():
            raise ValueError("Jira ticket title is required.")

        if not isinstance(description, str) or not description.strip():
            raise ValueError("Jira ticket description is required.")

        parameters["title"] = title.strip()
        parameters["description"] = description.strip()

    elif workflow_id == "WF003":

        recipient = parameters.get("recipient")
        subject = parameters.get("subject")
        message = parameters.get("message")

        if not isinstance(recipient, str) or not recipient.strip():
            raise ValueError("Email recipient is required.")

        if not re.fullmatch(
            r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}",
            recipient.strip(),
        ):
            raise ValueError("Invalid email address.")

        if not isinstance(subject, str) or not subject.strip():
            raise ValueError("Email subject is required.")

        if not isinstance(message, str) or not message.strip():
            raise ValueError("Email message is required.")

        parameters["recipient"] = recipient.strip()
        parameters["subject"] = subject.strip()
        parameters["message"] = message.strip()

    elif workflow_id == "WF004":

        # An omitted or blank zone means All zones.
        zone = parameters.get("zone")

        if zone is None or (
            isinstance(zone, str) and not zone.strip()
        ):
            parameters.pop("zone", None)

        elif not isinstance(zone, str):
            raise ValueError("Zone must be a valid string.")

        else:
            available_zones = get_available_zones()

            matched_zone = next(
                (
                    available_zone
                    for available_zone in available_zones
                    if available_zone.casefold()
                    == zone.strip().casefold()
                ),
                None,
            )

            if not matched_zone:
                raise ValueError(
                    f"Zone '{zone}' not found. "
                    f"Available zones: {', '.join(available_zones)}"
                )

            parameters["zone"] = matched_zone

        if "hours" in parameters:

            hours = parameters["hours"]

            if isinstance(hours, bool):
                raise ValueError(
                    "Hours must be a positive number."
                )

            try:
                hours = float(hours)
            except (TypeError, ValueError):
                raise ValueError(
                    "Hours must be a valid number."
                )

            if hours <= 0:
                raise ValueError(
                    "The number of hours must be greater than zero."
                )

            parameters["hours"] = hours

    else:
        raise ValueError(
            f"Unsupported workflow ID: {workflow_id}"
        )

    return parameters
