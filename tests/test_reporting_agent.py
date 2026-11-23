
from app.services.execution_service import execute_workflow
from app.agents.reporting_agent import generate_report


def main():
    execution_result = execute_workflow("WF001")

    report = generate_report(execution_result)

    print("===== WORKFLOW REPORT =====")
    print("WORKFLOW:", report["workflow_name"])
    print("TOTAL ALERTS:", report["total_alerts"])
    print("UNRESOLVED:", report["unresolved_alert_count"])
    print("SUMMARY:", report["summary"])

    print("\n===== ALERT DETAILS =====")

    for alert in report["alert_details"]:
        print(alert)


if __name__ == "__main__":
    main()
