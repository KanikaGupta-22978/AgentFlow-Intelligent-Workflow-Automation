
from app.services.execution_service import execute_workflow


def main():
    print("===== WF003 EMAIL NOTIFICATION TEST =====")

    email_data = {
        "recipient": "admin@example.com",
        "subject": "Network Alert Notification",
        "message": (
            "A high-priority network alert has been detected. "
            "Please investigate immediately."
        )
    }

    result = execute_workflow(
        "WF003",
        email_data,
    )

    print("\nWORKFLOW:", result["workflow_name"])
    print("WORKFLOW ID:", result["workflow_id"])
    print("PLUGIN RESULT:", result["plugin_result"])


if __name__ == "__main__":
    main()
