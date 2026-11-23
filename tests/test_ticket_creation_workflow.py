
from app.services.execution_service import execute_workflow


def main():
    print("===== WF002 TICKET CREATION TEST =====")

    ticket_data = {
        "title": "Network Connectivity Issue",
        "description": (
            "Network connectivity failure detected. "
            "Please investigate the affected device."
        )
    }

    result = execute_workflow(
        "WF002",
        ticket_data,
    )

    print("WORKFLOW:", result["workflow_name"])
    print("WORKFLOW ID:", result["workflow_id"])
    print("PLUGIN RESULT:", result["plugin_result"])


if __name__ == "__main__":
    main()
