
from abc import ABC, abstractmethod
from typing import Any


class BasePlugin(ABC):
    """
    Base interface for all plugins.
    Every plugin must implement execute().
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the plugin operation.
        """
        pass
