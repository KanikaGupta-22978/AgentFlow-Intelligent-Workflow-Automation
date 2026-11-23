
from datetime import datetime

from sqlalchemy.orm import Session

from app.services.dynamic_workflow_service import (
    get_dynamic_workflow_by_id,
)

from app.services.execution_service import (
    execute_daily_alert_summary,
    execute_performance_report,
    execute_ticket_creation,
    execute_email_notification,
)

from app.database.models import WorkflowExecution


def evaluate_condition(condition, context):
    """Evaluate a workflow step condition."""

    if not condition:
        return True

    field = condition.get("field")
    operator = condition.get("operator")
    expected_value = condition.get("value")

    actual_value = context.get(field)

    if operator == "equals":
        return actual_value == expected_value

    elif operator == "not_equals":
        return actual_value != expected_value

    elif operator == "greater_than":
        return actual_value is not None and actual_value > expected_value

    elif operator == "less_than":
        return actual_value is not None and actual_value < expected_value

    elif operator == "contains":
        return (
            actual_value is not None
            and expected_value in actual_value
        )

    else:
        raise ValueError(
            f"Unsupported condition operator: {operator}"
        )


def execute_dynamic_workflow(
    db: Session,
    workflow_id: int,
    input_data: dict | None = None,
):
    """Execute a dynamic workflow and save execution history."""

    workflow = get_dynamic_workflow_by_id(db, workflow_id)

    if not workflow:
        raise ValueError("Dynamic workflow not found.")

    if not workflow.is_active:
        raise ValueError("This dynamic workflow is inactive.")

    definition = workflow.definition or {}
    steps = definition.get("steps", [])

    execution = WorkflowExecution(
        workflow_id=workflow.id,
        status="running",
        input_data=input_data or {},
    )

    db.add(execution)
    db.commit()
    db.refresh(execution)

    step_results = []
    context = input_data.copy() if input_data else {}

    try:
        for step in steps:
            action = step.get("action")
            parameters = step.get("parameters", {})
            condition = step.get("condition")

            if not evaluate_condition(condition, context):
                step_results.append({
                    "step_id": step.get("step_id"),
                    "action": action,
                    "status": "skipped",
                    "message": "Step condition was not satisfied.",
                })
                continue

            # Fetch unresolved alerts
            if action == "fetch_alerts":
                alert_result = execute_daily_alert_summary()

                result = {
                    "alerts": alert_result.get(
                        "unresolved_alerts", []
                    ),
                    "total_alerts": alert_result.get(
                        "total_alerts", 0
                    ),
                    "unresolved_alert_count": alert_result.get(
                        "unresolved_alert_count", 0
                    ),
                }

            # Summarize alerts fetched by the previous step
            elif action == "summarize_alerts":
                alerts = context.get("alerts", [])

                result = {
                    "summary": (
                        f"{len(alerts)} unresolved alerts found."
                    ),
                    "unresolved_alert_count": len(alerts),
                    "alert_details": [
                        {
                            "device": alert.get("device/link"),
                            "intensity": alert.get("intensity"),
                            "ip_address": alert.get("ip_address"),
                        }
                        for alert in alerts
                    ],
                }

            elif action == "generate_alert_summary":
                result = execute_daily_alert_summary()

            elif action == "generate_performance_report":
                result = execute_performance_report(parameters)

            elif action == "create_jira_ticket":
                if not parameters.get("title"):
                    raise ValueError(
                        "A title is required to create a Jira ticket."
                    )

                result = execute_ticket_creation(parameters)

            elif action == "send_email":
                result = execute_email_notification(parameters)

            else:
                raise ValueError(
                    f"Unsupported dynamic workflow action: {action}"
                )

            context.update(result)

            step_results.append({
                "step_id": step.get("step_id"),
                "action": action,
                "status": "success",
                "result": result,
            })

        final_result = {
            "workflow_id": workflow.id,
            "workflow_name": workflow.name,
            "status": "success",
            "total_steps": len(steps),
            "step_results": step_results,
        }

        execution.status = "success"
        execution.output_data = final_result
        execution.completed_at = datetime.now()

        db.commit()

        final_result["execution_id"] = execution.id

        return final_result

    except Exception as error:
        execution.status = "failed"
        execution.error_message = str(error)
        execution.output_data = {
            "step_results": step_results,
        }
        execution.completed_at = datetime.now()

        db.commit()
        raise
