
from typing import Any

from sqlalchemy.orm import Session

from app.plugins.jira_plugin import JiraPlugin
from app.plugins.email_plugin import EmailPlugin


class PluginRegistry:
    """
    Central registry to manage and execute available plugins.
    """

    def __init__(self, db: Session):
        self.plugins = {
            "jira": JiraPlugin(db),
            "email": EmailPlugin(),
        }

    def get_plugin(self, plugin_name: str):
        plugin = self.plugins.get(plugin_name.lower())

        if plugin is None:
            raise ValueError(
                f"Plugin '{plugin_name}' is not registered."
            )

        return plugin

    def execute_plugin(
        self,
        plugin_name: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        plugin = self.get_plugin(plugin_name)
        return plugin.execute(data)

    def list_plugins(self) -> list[str]:
        return list(self.plugins.keys())
