
import os
import json
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
- Do not replace the title or description with generic text.
- Do not invent missing values.
- Project is configured separately and does not need extraction.

WF003: recipient, subject, message.

WF004: zone, hours.

For WF004:
- Select the exact zone name from the available zones.
- If the user mentions only a partial zone name,
  return the matching full zone name.
- Extract the requested number of hours.

For WF003:
- Extract recipient, subject and message.

Do not invent missing values.
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
    """Execute the selected workflow."""

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
