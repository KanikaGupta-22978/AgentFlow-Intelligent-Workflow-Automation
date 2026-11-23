
from app.agents.plugin_selection_agent import select_plugin


def main():
    workflow_ids = ["WF001", "WF002", "WF003", "WF004"]

    for workflow_id in workflow_ids:
        plugin = select_plugin(workflow_id)

        print(
            f"Workflow: {workflow_id} | "
            f"Selected Plugin: {plugin or 'No external plugin'}"
        )


if __name__ == "__main__":
    main()
