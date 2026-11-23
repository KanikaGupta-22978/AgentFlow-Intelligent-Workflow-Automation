
from typing import Any, Optional
from pydantic import BaseModel, Field


class WorkflowCondition(BaseModel):
    field: str
    operator: str
    value: Any


class WorkflowStep(BaseModel):
    step_id: str
    action: str
    description: Optional[str] = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    condition: Optional[WorkflowCondition] = None


class DynamicWorkflowCreate(BaseModel):
    name: str
    description: str
    trigger: Optional[str] = None
    steps: list[WorkflowStep] = Field(min_length=1)


class DynamicWorkflowResponse(BaseModel):
    workflow_id: int
    name: str
    description: str
    trigger: Optional[str] = None
    steps: list[WorkflowStep]
    status: str
