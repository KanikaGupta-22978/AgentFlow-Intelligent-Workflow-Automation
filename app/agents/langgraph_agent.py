
import os
import json
import re
from typing import TypedDict, Any

from dotenv import load_dotenv
from google import genai
from google.genai import types
from langgraph.graph import StateGraph, END

from app.agents.workflow_selection_agent import (
    select_workflow,
    extract_parameters,
    validate_parameters,
)
from app.services.execution_service import execute_workflow
from app.services.data_service import get_available_zones


load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

ALLOWED_PARAMETERS = {
    "WF001": [],
    "WF002": ["title", "description"],
    "WF003": ["recipient", "subject", "message"],
    "WF004": ["zone", "hours"],
}


class AgentState(TypedDict):
    user_instruction: str
    workflow_id: str
    parameters: dict[str, Any]
    llm_parameters: dict[str, Any]
    status: str
    error: str
    execution_result: dict[str, Any]
    llm_used: bool
    llm_warning: str


def understand_instruction(user_instruction: str) -> dict:
    """Use Gemini to understand the user's workflow request."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing.")

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=60000),
    )

    available_zones = get_available_zones()

    prompt = f"""
You are the natural-language understanding component of AgentFlow.

Available workflows:
WF001: Daily Alert Summary.
WF002: Ticket Creation using Jira.
WF003: Email Notification.
WF004: Network Performance Report.

Available zones:
{json.dumps(available_zones)}

Extract the workflow ID and relevant parameters.

Parameter rules:

WF001: no parameters.

WF002:
- Extract the exact Jira ticket title as "title".
- Extract the complete Jira ticket description as "description".
- Preserve the user's wording.
- Do not invent missing values.

WF003:
- Extract recipient, subject and message.
- Do not invent missing values.

WF004:
- Extract zone and hours.
- Select the exact zone name from available zones.
- Match partial zone names when possible.
- Extract the requested number of hours.

Do not execute workflows.

Return ONLY valid JSON:
{{
    "workflow_id": "WF001, WF002, WF003, WF004, or NONE",
    "parameters": {{}}
}}

User instruction:
{user_instruction}
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0,
        ),
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    result = json.loads(response.text)

    workflow_id = result.get("workflow_id")
    parameters = result.get("parameters", {})

    if workflow_id not in ALLOWED_PARAMETERS:
        raise ValueError(
            "Gemini could not identify a supported workflow."
        )

    if not isinstance(parameters, dict):
        raise ValueError("Gemini returned invalid parameters.")

    allowed_keys = ALLOWED_PARAMETERS[workflow_id]

    return {
        "workflow_id": workflow_id,
        "parameters": {
            key: value
            for key, value in parameters.items()
            if key in allowed_keys
        },
    }


def workflow_selection_node(state: AgentState) -> dict:
    """Try Gemini first and use rule-based fallback if necessary."""

    try:
        result = understand_instruction(
            state["user_instruction"]
        )

        return {
            "workflow_id": result["workflow_id"],
            "llm_parameters": result["parameters"],
            "llm_used": True,
            "llm_warning": "",
            "status": "workflow_selected",
            "error": "",
        }

    except Exception as gemini_error:
        try:
            workflow_id = select_workflow(
                state["user_instruction"]
            )

            return {
                "workflow_id": workflow_id,
                "llm_parameters": {},
                "llm_used": False,
                "llm_warning": (
                    "Gemini unavailable; rule-based fallback used: "
                    f"{str(gemini_error)[:200]}"
                ),
                "status": "workflow_selected",
                "error": "",
            }

        except ValueError as fallback_error:
            return {
                "workflow_id": "",
                "llm_parameters": {},
                "llm_used": False,
                "llm_warning": str(gemini_error)[:200],
                "status": "failed",
                "error": str(fallback_error),
            }


def normalize_zone_name(parameters: dict) -> dict:
    """Match partial zone names to exact database zone names."""

    requested_zone = parameters.get("zone")

    if not requested_zone:
        return parameters

    available_zones = get_available_zones()
    requested_zone = str(requested_zone).strip()

    matched_zone = next(
        (
            zone
            for zone in available_zones
            if zone.casefold() == requested_zone.casefold()
        ),
        None,
    )

    if not matched_zone:
        matched_zone = next(
            (
                zone
                for zone in available_zones
                if zone.casefold().startswith(
                    requested_zone.casefold() + " "
                )
            ),
            None,
        )

    if matched_zone:
        parameters["zone"] = matched_zone

    return parameters


def parameter_extraction_node(state: AgentState) -> dict:
    """Merge extracted parameters and validate them."""

    try:
        workflow_id = state["workflow_id"]

        existing_parameters = extract_parameters(
            workflow_id,
            state["user_instruction"],
        )

        llm_parameters = state.get("llm_parameters", {})

        parameters = {
            **existing_parameters,
            **llm_parameters,
        }

        if workflow_id == "WF004":
            parameters = normalize_zone_name(parameters)

        validated_parameters = validate_parameters(
            workflow_id,
            parameters,
        )

        return {
            "parameters": validated_parameters,
            "status": "parameters_validated",
            "error": "",
        }

    except Exception as error:
        return {
            "parameters": {},
            "status": "failed",
            "error": str(error),
        }


def workflow_execution_node(state: AgentState) -> dict:
    """Execute the selected individual workflow."""

    try:
        result = execute_workflow(
            state["workflow_id"],
            state["parameters"],
        )

        return {
            "execution_result": result,
            "status": "success",
            "error": "",
        }

    except Exception as error:
        return {
            "execution_result": {},
            "status": "failed",
            "error": str(error),
        }


def is_compound_report_request(instruction: str) -> bool:
    """Identify report requests that explicitly request another action."""

    text = instruction.casefold()

    has_report = any(
        phrase in text
        for phrase in ("performance report", "performance summary")
    ) or bool(re.search(r"\breport\b", text))

    has_email = bool(
        re.search(
            r"\b(email|e-mail|send mail|send an email|mail it)\b",
            text,
        )
    )

    has_jira = bool(
        re.search(
            r"\b(jira|ticket|create tickets?)\b",
            text,
        )
    )

    return has_report and (has_email or has_jira)


def build_jira_description(report: dict) -> str:
    """Build one Jira description containing all DOWN links."""

    down_links = report.get("down_links", [])

    lines = [
        "Critical network performance incident summary.",
        "",
        f"Zone: {report.get('zone', 'All zones')}",
        f"Total DOWN links: {len(down_links)}",
        "",
        "Affected links:",
    ]

    for index, link in enumerate(down_links, start=1):
        lines.extend([
            "",
            f"{index}. Site: {link.get('site_code') or 'N/A'}",
            f"   Link: {link.get('link') or 'N/A'}",
            f"   Zone: {link.get('zone') or 'N/A'}",
            f"   ISP: {link.get('isp') or 'N/A'}",
            f"   IP address: {link.get('ip_address') or 'N/A'}",
            f"   Circuit ID: {link.get('circuit_id') or 'N/A'}",
            f"   Uptime: {link.get('uptime')}",
        ])

    lines.extend([
        "",
        "Please investigate the affected links and restore service.",
        "Generated automatically by AgentFlow.",
    ])

    return "\n".join(lines)


def execute_compound_report_request(
    user_instruction: str,
) -> dict[str, Any]:
    """
    Execute a performance report followed by explicitly requested
    Jira ticket creation and/or email delivery.
    """

    text = user_instruction.casefold()

    email_requested = bool(
        re.search(
            r"\b(email|e-mail|send mail|send an email|mail it)\b",
            text,
        )
    )

    jira_requested = bool(
        re.search(
            r"\b(jira|ticket|create tickets?)\b",
            text,
        )
    )

    recipient = None

    if email_requested:
        email_match = re.search(
            r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}",
            user_instruction,
        )

        if not email_match:
            raise ValueError(
                "Please provide an email address to receive the report."
            )

        recipient = email_match.group(0)

    # Extract and validate WF004 parameters.
    report_parameters = extract_parameters(
        "WF004",
        user_instruction,
    )

    report_parameters = normalize_zone_name(report_parameters)

    report_parameters = validate_parameters(
        "WF004",
        report_parameters,
    )

    # Step 1: Generate the performance report.
    performance_report = execute_workflow(
        "WF004",
        report_parameters,
    )

    action_results = {
        "performance_report": {
            "status": "success",
            "result": performance_report,
        },
        "jira_ticket": {
            "status": "not_requested",
            "result": None,
        },
        "email_notification": {
            "status": "not_requested",
            "result": None,
        },
    }

    errors = []

    # Step 2: Create one Jira ticket containing all DOWN links.
    if jira_requested:
        down_links = performance_report.get("down_links", [])

        if not down_links:
            action_results["jira_ticket"] = {
                "status": "skipped",
                "message": (
                    "No DOWN links were found. "
                    "No Jira ticket was created."
                ),
                "result": None,
            }
        else:
            jira_parameters = {
                "title": (
                    f"Network DOWN Link Incident - "
                    f"{performance_report.get('zone', 'All zones')} "
                    f"({len(down_links)} affected links)"
                ),
                "description": build_jira_description(
                    performance_report
                ),
            }

            try:
                jira_result = execute_workflow(
                    "WF002",
                    jira_parameters,
                )

                action_results["jira_ticket"] = {
                    "status": "success",
                    "result": jira_result,
                }

            except Exception as error:
                errors.append(f"Jira: {str(error)}")

                action_results["jira_ticket"] = {
                    "status": "failed",
                    "error": str(error),
                }

    # Step 3: Email the complete performance report.
    if email_requested:
        email_parameters = {
            "recipient": recipient,
            "subject": (
                f"Performance Summary Report - "
                f"{performance_report.get('zone', 'All zones')}"
            ),
            "message": "Please find the complete performance report below.",
            "report_data": performance_report,
        }

        try:
            email_result = execute_workflow(
                "WF003",
                email_parameters,
            )

            action_results["email_notification"] = {
                "status": "success",
                "result": email_result,
            }

        except Exception as error:
            errors.append(f"Email: {str(error)}")

            action_results["email_notification"] = {
                "status": "failed",
                "error": str(error),
            }

    # Preserve useful top-level fields for the existing API/reporting code.
    email_result = action_results["email_notification"].get("result")
    jira_result = action_results["jira_ticket"].get("result")

    result = {
        **performance_report,
        "workflow_id": "WF004+COMPOUND",
        "workflow_name": "Performance Report and Follow-up Actions",
        "performance_report": performance_report,
        "jira_result": jira_result,
        "email_result": email_result,
        "plugin_result": (
            email_result.get("plugin_result")
            if isinstance(email_result, dict)
            else None
        ),
        "action_results": action_results,
    }

    failed_actions = [
        action
        for action in ("jira_ticket", "email_notification")
        if action_results[action]["status"] == "failed"
    ]

    if failed_actions:
        status = "partial_success"
    else:
        status = "success"

    return {
        "workflow_id": "WF004+COMPOUND",
        "parameters": {
            **report_parameters,
            "recipient": recipient,
        },
        "execution_result": result,
        "status": status,
        "error": "; ".join(errors),
        "llm_used": False,
        "llm_warning": "",
    }


def route_after_selection(state: AgentState):
    return (
        END
        if state["status"] == "failed"
        else "parameter_extraction"
    )


def route_after_parameter_extraction(state: AgentState):
    return (
        END
        if state["status"] == "failed"
        else "workflow_execution"
    )


graph_builder = StateGraph(AgentState)

graph_builder.add_node(
    "workflow_selection",
    workflow_selection_node,
)

graph_builder.add_node(
    "parameter_extraction",
    parameter_extraction_node,
)

graph_builder.add_node(
    "workflow_execution",
    workflow_execution_node,
)

graph_builder.set_entry_point("workflow_selection")

graph_builder.add_conditional_edges(
    "workflow_selection",
    route_after_selection,
    {
        "parameter_extraction": "parameter_extraction",
        END: END,
    },
)

graph_builder.add_conditional_edges(
    "parameter_extraction",
    route_after_parameter_extraction,
    {
        "workflow_execution": "workflow_execution",
        END: END,
    },
)

graph_builder.add_edge(
    "workflow_execution",
    END,
)

workflow_graph = graph_builder.compile()


def run_agent(user_instruction: str) -> dict[str, Any]:
    """Understand, validate and execute a natural-language request."""

    if not isinstance(user_instruction, str) or not user_instruction.strip():
        return {
            "workflow_id": "",
            "parameters": {},
            "execution_result": {},
            "status": "failed",
            "error": "Please provide a workflow instruction.",
            "llm_used": False,
            "llm_warning": "",
        }

    # Handle explicit report + email/Jira requests before single-workflow
    # selection. Existing individual workflow requests still use the graph.
    if is_compound_report_request(user_instruction):
        try:
            return execute_compound_report_request(user_instruction)
        except Exception as error:
            return {
                "workflow_id": "WF004+COMPOUND",
                "parameters": {},
                "execution_result": {},
                "status": "failed",
                "error": str(error),
                "llm_used": False,
                "llm_warning": "",
            }

    initial_state = {
        "user_instruction": user_instruction,
        "workflow_id": "",
        "parameters": {},
        "llm_parameters": {},
        "status": "started",
        "error": "",
        "execution_result": {},
        "llm_used": False,
        "llm_warning": "",
    }

    return workflow_graph.invoke(initial_state)
