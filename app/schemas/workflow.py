
from typing import Any, Optional
from pydantic import BaseModel, Field


class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    workflow_type: str
    definition: Optional[dict[str, Any]] = None


class WorkflowResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    workflow_type: str
    is_active: bool

    class Config:
        from_attributes = True


class WorkflowExecuteRequest(BaseModel):
    workflow_id: Optional[int] = None
    user_instruction: str = Field(
        ...,
        min_length=1,
        description="Natural-language instruction to execute a workflow"
    )
    input_data: Optional[dict[str, Any]] = None
