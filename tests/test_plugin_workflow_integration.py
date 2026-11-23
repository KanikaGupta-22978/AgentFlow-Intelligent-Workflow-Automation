
from app.services.execution_service import execute_plugin_for_workflow


def main():
    print("===== PLUGIN WORKFLOW INTEGRATION TEST =====")

    # Test WF002 - Jira
    jira_result = execute_plugin_for_workflow(
        "WF002",
        {
            "title": "Network Alert Ticket",
            "description": "A network issue requires investigation."
        }
    )

    print("\nJIRA RESULT:", jira_result)

    # Test WF003 - Email
    email_result = execute_plugin_for_workflow(
        "WF003",
        {
            "recipient": "admin@example.com",
            "subject": "Network Alert",
            "message": "A network issue has been detected."
        }
    )

    print("\nEMAIL RESULT:", email_result)

    # Test WF001 - No external plugin
    other_result = execute_plugin_for_workflow("WF001", {})

    print("\nWF001 RESULT:", other_result)


if __name__ == "__main__":
    main()
