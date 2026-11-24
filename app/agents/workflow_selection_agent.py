
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

    if any(word in instruction for word in ["email", "notification", "send mail"]):
        return "WF003"

    if any(word in instruction for word in ["alert", "alerts"]):
        return "WF001"

    if any(word in instruction for word in ["performance", "report"]):
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

    if workflow_id == "WF004":
        zones = get_available_zones()

        matched_zone = next(
            (
                zone for zone in zones
                if zone.casefold() in instruction.casefold()
            ),
            None,
        )

        zone_match = re.search(
            r"\bfor\s+(.+?)(?=\s+for\s+the\s+last\b|\s+last\b|$)",
            instruction,
            re.IGNORECASE,
        )

        if matched_zone:
            parameters["zone"] = matched_zone
        elif zone_match:
            requested_zone = zone_match.group(1).strip()
            if requested_zone:
                parameters["zone"] = requested_zone

        duration_match = re.search(
            r"last\s+(\d+)\s+hours?",
            instruction,
            re.IGNORECASE,
        )

        if duration_match:
            parameters["hours"] = int(duration_match.group(1))

    elif workflow_id == "WF003":
        email_match = re.search(
            r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}",
            instruction,
        )

        if email_match:
            parameters["recipient"] = email_match.group(0)

        subject_match = re.search(
            r"subject\s*:\s*(.+?)(?=\s+message\s*:|$)",
            instruction,
            re.IGNORECASE,
        )

        if subject_match:
            parameters["subject"] = subject_match.group(1).strip()

        message_match = re.search(
            r"message\s*:\s*(.+)$",
            instruction,
            re.IGNORECASE,
        )

        if message_match:
            parameters["message"] = message_match.group(1).strip()

    return parameters


def validate_parameters(
    workflow_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """Validate extracted parameters before workflow execution."""

    if workflow_id == "WF004":
        if "zone" in parameters:
            available_zones = get_available_zones()

            matched_zone = next(
                (
                    zone for zone in available_zones
                    if zone.casefold() == parameters["zone"].casefold()
                ),
                None,
            )

            if not matched_zone:
                raise ValueError(
                    f"Zone '{parameters['zone']}' not found. "
                    f"Available zones: {', '.join(available_zones)}"
                )

            parameters["zone"] = matched_zone

        if "hours" in parameters:
            if float(parameters["hours"]) <= 0:
                raise ValueError(
                    "The number of hours must be greater than zero."
                )

    elif workflow_id == "WF003":
        recipient = parameters.get("recipient")
        subject = parameters.get("subject")
        message = parameters.get("message")

        if not recipient:
            raise ValueError("Email recipient is required.")

        if not isinstance(recipient, str) or not re.fullmatch(
            r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}",
            recipient.strip(),
        ):
            raise ValueError("Invalid email address.")

        if not subject or not isinstance(subject, str) or not subject.strip():
            raise ValueError("Email subject is required.")

        if not message or not isinstance(message, str) or not message.strip():
            raise ValueError("Email message is required.")

        parameters["recipient"] = recipient.strip()
        parameters["subject"] = subject.strip()
        parameters["message"] = message.strip()

    return parameters
