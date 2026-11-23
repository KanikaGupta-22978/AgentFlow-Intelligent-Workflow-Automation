
from app.agents.workflow_selection_agent import select_workflow


def main():
    test_instructions = [
        "Show me the latest alerts",
        "Create a Jira ticket",
        "Send an email notification",
        "Generate a performance report",
    ]

    for instruction in test_instructions:
        workflow_id = select_workflow(instruction)

        print(
            f"Instruction: {instruction}\n"
            f"Selected Workflow: {workflow_id}\n"
        )


if __name__ == "__main__":
    main()
