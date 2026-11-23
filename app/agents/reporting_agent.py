
def generate_report(execution_result: dict) -> dict:
    """Generate readable reports for alert and plugin workflows."""

    workflow_name = execution_result.get(
        "workflow_name", "Unknown Workflow"
    )

    # Existing alert-summary reporting
    total_alerts = execution_result.get("total_alerts", 0)
    unresolved_alerts = execution_result.get("unresolved_alerts", [])

    report = {
        "workflow_name": workflow_name,
        "total_alerts": total_alerts,
        "unresolved_alert_count": len(unresolved_alerts),
        "summary": (
            f"{len(unresolved_alerts)} unresolved alerts "
            f"found out of {total_alerts} total alerts."
        ),
        "alert_details": [
            {
                "device": alert.get("device/link"),
                "intensity": alert.get("intensity"),
                "ip_address": alert.get("ip_address"),
            }
            for alert in unresolved_alerts
        ],
    }

    # Additional reporting for plugin workflows
    plugin_result = execution_result.get("plugin_result")

    if isinstance(plugin_result, dict):
        plugin_name = plugin_result.get("plugin")

        report["plugin"] = plugin_name
        report["plugin_success"] = plugin_result.get("success", False)

        if plugin_name == "jira":
            ticket_id = plugin_result.get("ticket_id")
            ticket_title = plugin_result.get("title")
            ticket_status = plugin_result.get("status")

            report["summary"] = (
                f"Jira ticket #{ticket_id} created successfully: "
                f"{ticket_title}. Status: {ticket_status}."
            )

            report["ticket_details"] = {
                "ticket_id": ticket_id,
                "title": ticket_title,
                "status": ticket_status,
            }

        elif plugin_name == "email":
            recipient = plugin_result.get("recipient")
            subject = plugin_result.get("subject")

            report["summary"] = (
                f"Email notification generated successfully "
                f"for {recipient}. Subject: {subject}."
            )

            report["email_details"] = {
                "recipient": recipient,
                "subject": subject,
                "message": plugin_result.get("message"),
            }

    return report
