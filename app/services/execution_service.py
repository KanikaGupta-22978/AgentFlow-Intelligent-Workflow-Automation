
from datetime import datetime, timedelta
from typing import Any

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


JIRA_KANBAN_BOARD_URL = (
    "https://mgpskanika5733.atlassian.net/"
    "jira/software/projects/KAN/boards/1?filter=&groupBy=none"
)


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


def _parse_timestamp(value: Any) -> datetime | None:
    """Parse a timestamp safely. Return None if it is missing or invalid."""

    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(str(value).strip())

        # Normalize timezone-aware timestamps to naive UTC so they
        # can safely be compared with other parsed timestamps.
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(
                datetime.now().astimezone().tzinfo
            ).replace(tzinfo=None)

        return parsed

    except (TypeError, ValueError):
        return None


def format_performance_report_email(report: dict) -> str:
    """Format the complete performance report as readable plain text."""

    period = report.get("reporting_period") or {}
    down_links = report.get("down_links") or []

    average_score = report.get("average_performance_score")

    lines = [
        "PERFORMANCE SUMMARY REPORT",
        "=" * 55,
        "",
        f"Zone: {report.get('zone', 'All zones')}",
        f"Total records included: {report.get('total_records', 0)}",
        (
            "Average performance score: "
            f"{average_score if average_score is not None else 'N/A'}"
        ),
        f"Total DOWN links: {report.get('down_link_count', len(down_links))}",
        (
            f"Reporting period: {period.get('start', 'N/A')} "
            f"to {period.get('end', 'N/A')}"
        ),
        "",
        "DATA QUALITY",
        "-" * 55,
        (
            "Records excluded because timestamps were missing: "
            f"{report.get('records_excluded_missing_timestamp', 0)}"
        ),
        (
            "Records excluded because timestamps were invalid: "
            f"{report.get('records_excluded_invalid_timestamp', 0)}"
        ),
        (
            "Records excluded because they were outside the requested period: "
            f"{report.get('records_excluded_outside_period', 0)}"
        ),
        report.get(
            "time_filter_note",
            "No time-based filtering was requested.",
        ),
        "",
        "=" * 55,
        "DOWN LINK DETAILS",
        "=" * 55,
        "",
    ]

    if not down_links:
        lines.append("No DOWN links found in the selected reporting period.")
    else:
        for index, link in enumerate(down_links, start=1):
            lines.extend([
                f"{index}. Site Code: {link.get('site_code') or 'N/A'}",
                f"   Link ID: {link.get('link') or 'N/A'}",
                f"   Zone: {link.get('zone') or 'N/A'}",
                f"   ISP: {link.get('isp') or 'N/A'}",
                f"   IP Address: {link.get('ip_address') or 'N/A'}",
                f"   Link Type: {link.get('link_type') or 'N/A'}",
                (
                    "   Link Speed (Mbps): "
                    f"{link.get('link_speed_mbps') or 'N/A'}"
                ),
                f"   Uptime: {link.get('uptime', 'N/A')}",
                (
                    "   Performance Score: "
                    f"{link.get('performance_score', 'N/A')}"
                ),
                f"   Average Latency: {link.get('avg_latency', 'N/A')}",
                f"   Average Packet Drop: {link.get('avg_packet_drop', 'N/A')}",
                f"   Average Jitter: {link.get('avg_jitter', 'N/A')}",
                f"   Average CPU: {link.get('avg_cpu', 'N/A')}",
                f"   Average Memory: {link.get('avg_memory', 'N/A')}",
                f"   Circuit ID: {link.get('circuit_id') or 'N/A'}",
                f"   Site Address: {link.get('site_address') or 'N/A'}",
                "",
            ])

    lines.extend([
        "=" * 55,
        "JIRA INCIDENT TRACKING",
        "=" * 55,
        "",
        "Use the following Jira Kanban board to track incident status:",
        JIRA_KANBAN_BOARD_URL,
        "",
        "Generated automatically by AgentFlow.",
    ])

    return "\n".join(lines)


def execute_email_notification(plugin_data: dict):
    """Send an email, including performance report data when supplied."""

    plugin_data = dict(plugin_data)

    report_data = plugin_data.pop("report_data", None)

    if report_data is not None:
        plugin_data["message"] = format_performance_report_email(
            report_data
        )

        plugin_data.setdefault(
            "subject",
            "Performance Summary Report",
        )

    result = execute_plugin_for_workflow("WF003", plugin_data)

    return {
        "workflow_id": "WF003",
        "workflow_name": "Email Notification",
        "plugin_result": result,
    }


def execute_performance_report(input_data: dict):
    """
    Generate a performance report.

    When hours are requested, only records with valid timestamps
    inside the requested reporting period are included.

    Records without timestamps are excluded from time-based
    calculations and counted separately.
    """

    records = load_performance_stats()
    metadata = load_performance_metadata()

    zone = input_data.get("zone")
    requested_hours = input_data.get("hours")

    # Filter records by zone first.
    if zone:
        requested_zone = str(zone).strip().casefold()

        records = [
            record
            for record in records
            if (record.get("site_zone") or "").strip().casefold()
            == requested_zone
        ]

    report_date = metadata.get("report_date") or {}

    report_start = report_date.get("start")
    report_end = report_date.get("end")

    filtered_start = report_start
    filtered_end = report_end

    time_filter_applied = False

    records_excluded_missing_timestamp = 0
    records_excluded_invalid_timestamp = 0
    records_excluded_outside_period = 0

    time_filter_note = "No time-based filtering was requested."

    # Apply timestamp filtering only when the user requests a period.
    if requested_hours is not None:

        try:
            hours = float(requested_hours)
        except (TypeError, ValueError):
            raise ValueError(
                "The requested reporting hours must be a valid number."
            )

        if hours <= 0:
            raise ValueError(
                "The requested reporting hours must be greater than zero."
            )

        if not report_end:
            raise ValueError(
                "Cannot apply time filter: reporting end time is missing."
            )

        end_time = _parse_timestamp(report_end)

        if end_time is None:
            raise ValueError(
                "Cannot apply time filter: reporting end time is invalid."
            )

        start_time = end_time - timedelta(hours=hours)

        filtered_start = start_time.isoformat()
        filtered_end = end_time.isoformat()

        timestamped_records = []

        for record in records:
            timestamp_value = record.get("timestamp")

            if not timestamp_value:
                records_excluded_missing_timestamp += 1
                continue

            record_time = _parse_timestamp(timestamp_value)

            if record_time is None:
                records_excluded_invalid_timestamp += 1
                continue

            if start_time <= record_time <= end_time:
                timestamped_records.append(record)
            else:
                records_excluded_outside_period += 1

        # IMPORTANT:
        # Do not add records without timestamps back into the report.
        records = timestamped_records

        time_filter_applied = True

        time_filter_note = (
            f"Report includes only records with valid timestamps "
            f"between {filtered_start} and {filtered_end}. "
            f"Records without timestamps or with invalid timestamps "
            f"were excluded."
        )

    # Identify DOWN links only from the records included in this report.
    down_links = [
        {
            "site_code": record.get("site_code"),
            "link": record.get("link"),
            "zone": record.get("site_zone"),
            "ip_address": record.get("IP"),
            "isp": record.get("isp"),
            "link_type": record.get("link_type"),
            "link_speed_mbps": record.get("link_speed (Mbps)"),
            "uptime": record.get("uptime"),
            "performance_score": record.get("performance_score"),
            "avg_latency": record.get("avg_latency"),
            "avg_packet_drop": record.get("avg_packet_drop"),
            "avg_jitter": record.get("avg_jitter"),
            "avg_cpu": record.get("avg_cpu"),
            "avg_memory": record.get("avg_memory"),
            "circuit_id": record.get("circuit_id"),
            "site_address": record.get("site_address"),
        }
        for record in records
        if record.get("uptime") is not None
        and float(record.get("uptime")) == 0
    ]

    # Calculate average performance score using included records only.
    performance_scores = [
        float(record["performance_score"])
        for record in records
        if record.get("performance_score") is not None
    ]

    average_score = (
        sum(performance_scores) / len(performance_scores)
        if performance_scores
        else None
    )

    # Explain when the dataset does not contain enough timestamped data.
    if requested_hours is not None and not records:
        message = (
            "No timestamped performance records were found in the "
            "requested reporting period. Records without timestamps "
            "were excluded and were not used in the calculations."
        )
    elif not records:
        message = (
            "No performance records were found for the requested zone."
        )
    else:
        message = None

    return {
        "workflow_id": "WF004",
        "workflow_name": "Performance Report",
        "zone": zone or "All zones",
        "total_records": len(records),
        "average_performance_score": (
            round(average_score, 2)
            if average_score is not None
            else None
        ),
        "down_link_count": len(down_links),
        "down_links": down_links,
        "reporting_period": {
            "start": filtered_start,
            "end": filtered_end,
        },
        "requested_hours": requested_hours,
        "time_filter_applied": time_filter_applied,
        "time_filter_note": time_filter_note,
        "records_excluded_missing_timestamp": (
            records_excluded_missing_timestamp
        ),
        "records_excluded_invalid_timestamp": (
            records_excluded_invalid_timestamp
        ),
        "records_excluded_outside_period": (
            records_excluded_outside_period
        ),
        "message": message,
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
