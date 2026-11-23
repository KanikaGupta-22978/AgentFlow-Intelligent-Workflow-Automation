
from app.services.execution_service import execute_from_instruction


def main():
    instruction = "Show me the latest alerts"

    result = execute_from_instruction(instruction)

    print("USER INSTRUCTION:", instruction)
    print("SELECTED WORKFLOW:", result["selected_workflow_id"])
    print("EXECUTION RESULT:", result["result"]["workflow_name"])
    print("TOTAL ALERTS:", result["result"]["total_alerts"])
    print("UNRESOLVED ALERTS:", result["result"]["unresolved_alert_count"])


if __name__ == "__main__":
    main()
