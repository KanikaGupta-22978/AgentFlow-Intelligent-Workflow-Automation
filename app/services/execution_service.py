
from datetime import datetime

from app.services.data_service import (
    load_alerts,
    load_performance_stats,
    load_performance_metadata,
)

from app.agents.workflow_selection_agent import select_workflow
from app.agents.plugin_selection_agent import select_plugin
from app.plugins.plugin_registry import PluginRegistry

from app.database.connection import SessionLocal
from app.database.models import WorkflowExecution


def execute_daily_alert_summary():
    """Generate a summary of unresolved DOWN and HIGH alerts."""

    alerts = load_alerts()

    unresolved_alerts = [
        alert
        for alert in alerts
        if alert.get("intensity") in ["DOWN", "HIGH"]
        and not alert.get("acknowledged", False)
    ]

    return {
        "workflow_id": "WF001",
        "workflow_name": "Daily Alert Summary",
        "total_alerts": len(alerts),
        "unresolved_alert_count": len(unresolved_alerts),
        "unresolved_alerts": unresolved_alerts,
    }


def execute_ticket_creation(plugin_data: dict):
    """Create a ticket using the Jira plugin."""

    result = execute_plugin_for_workflow("WF002", plugin_data)

    return {
        "workflow_id": "WF002",
        "workflow_name": "Ticket Creation",
        "plugin_result": result,
    }


def execute_email_notification(plugin_data: dict):
    """Generate an email notification using the Email plugin."""

    result = execute_plugin_for_workflow("WF003", plugin_data)

    return {
        "workflow_id": "WF003",
        "workflow_name": "Email Notification",
        "plugin_result": result,
    }


def execute_performance_report(input_data: dict):
    """Generate a performance report with available reporting-period metadata."""

    records = load_performance_stats()
    metadata = load_performance_metadata()

    zone = input_data.get("zone")
    requested_hours = input_data.get("hours")

    if zone:
        records = [
            record for record in records
            if record.get("site_zone", "").casefold() == zone.casefold()
        ]

    report_date = metadata.get("report_date") or {}
    report_start = report_date.get("start")
    report_end = report_date.get("end")

    if not records:
        return {
            "workflow_id": "WF004",
            "workflow_name": "Performance Report",
            "zone": zone,
            "total_records": 0,
            "reporting_period": {
                "start": report_start,
                "end": report_end,
            },
            "requested_hours": requested_hours,
            "time_filter_applied": False,
            "message": "No performance records found for the requested zone.",
            "records": [],
        }

    performance_scores = [
        record["performance_score"]
        for record in records
        if record.get("performance_score") is not None
    ]

    average_score = (
        sum(performance_scores) / len(performance_scores)
        if performance_scores else None
    )

    return {
        "workflow_id": "WF004",
        "workflow_name": "Performance Report",
        "zone": zone or "All zones",
        "total_records": len(records),
        "average_performance_score": round(average_score, 2)
        if average_score is not None else None,
        "reporting_period": {
            "start": report_start,
            "end": report_end,
        },
        "requested_hours": requested_hours,
        "time_filter_applied": False,
        "time_filter_note": (
            "The requested duration was extracted, but individual "
            "performance records do not contain timestamps. "
            "Records are filtered by zone only, not by time."
            if requested_hours
            else "No time-based filtering was requested."
        ),
        "records": records,
    }


def execute_workflow_without_history(
    workflow_id: str,
    input_data: dict | None = None,
):
    """Execute the selected workflow."""

    input_data = input_data or {}

    if workflow_id == "WF001":
        return execute_daily_alert_summary()

    if workflow_id == "WF002":
        return execute_ticket_creation(input_data)

    if workflow_id == "WF003":
        return execute_email_notification(input_data)

    if workflow_id == "WF004":
        return execute_performance_report(input_data)

    raise ValueError(
        f"Workflow '{workflow_id}' is not implemented yet."
    )


def execute_workflow(
    workflow_id: str,
    input_data: dict | None = None,
):
    """Execute a workflow and save its execution history."""

    db = SessionLocal()

    execution = WorkflowExecution(
        workflow_id=None,
        status="running",
        input_data={
            "workflow_id": workflow_id,
            "input_data": input_data or {},
        },
    )

    db.add(execution)
    db.commit()
    db.refresh(execution)

    try:
        result = execute_workflow_without_history(
            workflow_id,
            input_data,
        )

        execution.status = "success"
        execution.output_data = result
        execution.completed_at = datetime.now()

        db.commit()

        return result

    except Exception as error:
        execution.status = "failed"
        execution.error_message = str(error)
        execution.completed_at = datetime.now()

        db.commit()
        raise

    finally:
        db.close()


def execute_plugin_for_workflow(
    workflow_id: str,
    plugin_data: dict,
):
    """Select and execute the plugin required by a workflow."""

    plugin_name = select_plugin(workflow_id)

    if plugin_name is None:
        return {
            "message": "No external plugin required."
        }

    db = SessionLocal()

    try:
        registry = PluginRegistry(db)

        return registry.execute_plugin(plugin_name, plugin_data)

    finally:
        db.close()


def execute_from_instruction(
    user_instruction: str,
    input_data: dict | None = None,
):
    """Select a workflow from a natural-language instruction."""

    workflow_id = select_workflow(user_instruction)

    result = execute_workflow(workflow_id, input_data)

    return {
        "selected_workflow_id": workflow_id,
        "result": result,
    }
