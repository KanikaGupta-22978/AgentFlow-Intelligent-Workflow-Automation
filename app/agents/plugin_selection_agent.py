
def select_plugin(workflow_id: str) -> str:
    """
    Select the required plugin based on the workflow ID.
    """

    plugin_mapping = {
        "WF001": None,
        "WF002": "jira",
        "WF003": "email",
        "WF004": None,
    }

    if workflow_id not in plugin_mapping:
        raise ValueError(
            f"No plugin mapping found for workflow: {workflow_id}"
        )

    return plugin_mapping[workflow_id]
