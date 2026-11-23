
from app.services.execution_service import execute_workflow


def main():
    result = execute_workflow("WF001")

    print("WORKFLOW NAME:", result["workflow_name"])
    print("TOTAL ALERTS:", result["total_alerts"])
    print("UNRESOLVED ALERTS:", result["unresolved_alert_count"])

    print("\nUNRESOLVED ALERT DETAILS:")

    for alert in result["unresolved_alerts"]:
        print(
            alert.get("device/link"),
            "|",
            alert.get("intensity"),
            "|",
            alert.get("acknowledged"),
        )


if __name__ == "__main__":
    main()
