
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.dependencies import get_db

from app.schemas.dynamic_workflow import (
    DynamicWorkflowCreate,
)

from app.services.dynamic_workflow_service import (
    create_dynamic_workflow,
    get_dynamic_workflows,
    get_dynamic_workflow_by_id,
)

from app.services.dynamic_workflow_execution_service import (
    execute_dynamic_workflow,
)


router = APIRouter(
    prefix="/dynamic-workflows",
    tags=["Dynamic Workflows"],
)


class DynamicWorkflowExecuteRequest(BaseModel):
    input_data: Optional[dict[str, Any]] = None


@router.post("/")
def create_new_dynamic_workflow(
    workflow_data: DynamicWorkflowCreate,
    db: Session = Depends(get_db),
):
    workflow = create_dynamic_workflow(db, workflow_data)

    return {
        "workflow_id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "trigger": workflow.definition.get("trigger"),
        "steps": workflow.definition.get("steps", []),
        "status": "created",
    }


@router.get("/")
def list_dynamic_workflows(
    db: Session = Depends(get_db),
):
    workflows = get_dynamic_workflows(db)

    return [
        {
            "workflow_id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "trigger": workflow.definition.get("trigger"),
            "steps": workflow.definition.get("steps", []),
            "status": "active" if workflow.is_active else "inactive",
        }
        for workflow in workflows
    ]


@router.get("/{workflow_id}")
def get_dynamic_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
):
    workflow = get_dynamic_workflow_by_id(db, workflow_id)

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail="Dynamic workflow not found.",
        )

    return {
        "workflow_id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "trigger": workflow.definition.get("trigger"),
        "steps": workflow.definition.get("steps", []),
        "status": "active" if workflow.is_active else "inactive",
    }


@router.post("/{workflow_id}/execute")
def run_dynamic_workflow(
    workflow_id: int,
    request: DynamicWorkflowExecuteRequest,
    db: Session = Depends(get_db),
):
    try:
        return execute_dynamic_workflow(
            db,
            workflow_id,
            request.input_data or {},
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )
