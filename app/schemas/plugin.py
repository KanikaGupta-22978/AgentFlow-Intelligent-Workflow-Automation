
from typing import Any, Optional
from pydantic import BaseModel


class PluginCreate(BaseModel):
    name: str
    description: Optional[str] = None
    configuration: Optional[dict[str, Any]] = None


class PluginResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_enabled: bool

    class Config:
        from_attributes = True
