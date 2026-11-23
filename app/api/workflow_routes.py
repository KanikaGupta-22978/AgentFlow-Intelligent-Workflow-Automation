
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowExecuteRequest,
)
from app.services.workflow_service import (
    create_workflow,
    get_all_workflows,
)
from app.services.execution_service import execute_workflow
from app.agents.langgraph_agent import run_agent
from app.agents.reporting_agent import generate_report


router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post("/", response_model=WorkflowResponse)
def create_new_workflow(
    workflow_data: WorkflowCreate,
    db: Session = Depends(get_db),
):
    return create_workflow(db, workflow_data)


@router.get("/", response_model=list[WorkflowResponse])
def list_workflows(db: Session = Depends(get_db)):
    return get_all_workflows(db)


@router.post("/execute")
def run_workflow(
    workflow_id: str,
    request_data: dict | None = None,
):
    try:
        input_data = request_data or {}

        result = execute_workflow(
            workflow_id,
            input_data,
        )

        report = generate_report(result)

        return {
            "status": "success",
            "result": result,
            "report": report,
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/execute-natural-language")
def run_workflow_from_instruction(
    request: WorkflowExecuteRequest,
):
    try:
        execution = run_agent(request.user_instruction)

        if execution["status"] == "failed":
            raise ValueError(execution["error"])

        result = execution["execution_result"]
        report = generate_report(result)

        return {
            "status": "success",
            "instruction": request.user_instruction,
            "selected_workflow_id": execution["workflow_id"],
            "extracted_parameters": execution["parameters"],
            "result": result,
            "report": report,
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
