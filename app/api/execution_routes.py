
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.database.models import WorkflowExecution, Workflow


router = APIRouter(
    prefix="/executions",
    tags=["Execution History"],
)


PREDEFINED_WORKFLOWS = {
    "WF001": "Daily Alert Summary",
    "WF002": "Jira Ticket Creation",
    "WF003": "Email Notification",
    "WF004": "Performance Report",
}


def get_workflow_information(execution, db: Session):
    """Identify predefined or dynamic workflow details."""

    if execution.workflow_id is not None:
        workflow = (
            db.query(Workflow)
            .filter(Workflow.id == execution.workflow_id)
            .first()
        )

        return {
            "workflow_id": execution.workflow_id,
            "workflow_name": (
                workflow.name
                if workflow
                else f"Dynamic Workflow #{execution.workflow_id}"
            ),
            "workflow_type": "dynamic",
        }

    input_data = execution.input_data or {}
    workflow_id = input_data.get("workflow_id")

    return {
        "workflow_id": workflow_id,
        "workflow_name": PREDEFINED_WORKFLOWS.get(
            workflow_id,
            "Unknown Workflow",
        ),
        "workflow_type": "predefined",
    }


def format_execution(execution, db: Session):
    """Format execution data for API responses."""

    workflow_info = get_workflow_information(execution, db)

    return {
        "execution_id": execution.id,
        **workflow_info,
        "status": execution.status,
        "input_data": execution.input_data,
        "output_data": execution.output_data,
        "error_message": execution.error_message,
        "started_at": execution.started_at,
        "completed_at": execution.completed_at,
    }


# --------------------------------------------------
# EXECUTION HISTORY WITH FILTERING AND PAGINATION
# --------------------------------------------------

@router.get("/")
def get_execution_history(
    status: str | None = Query(
        default=None,
        description="Filter by success, failed, or running",
    ),
    workflow_id: str | None = Query(
        default=None,
        description="Filter by workflow ID, e.g. WF001 or 9",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(WorkflowExecution)

    # Filter by execution status
    if status:
        status = status.strip().lower()

        if status not in ["success", "failed", "running"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid status. Use success, failed, or running.",
            )

        query = query.filter(
            WorkflowExecution.status == status
        )

    # Filter by workflow ID
    if workflow_id:
        workflow_id = workflow_id.strip()

        if workflow_id.isdigit():
            query = query.filter(
                WorkflowExecution.workflow_id == int(workflow_id)
            )
        else:
            query = query.filter(
                WorkflowExecution.input_data["workflow_id"].as_string()
                == workflow_id
            )

    # Count records after applying filters
    total = query.count()

    # Apply pagination
    executions = (
        query
        .order_by(WorkflowExecution.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size) if total else 0,
        "executions": [
            format_execution(execution, db)
            for execution in executions
        ],
    }


# --------------------------------------------------
# DASHBOARD SUMMARY
# --------------------------------------------------

@router.get("/summary")
def get_execution_summary(
    db: Session = Depends(get_db),
):
    total = db.query(WorkflowExecution).count()

    successful = (
        db.query(WorkflowExecution)
        .filter(WorkflowExecution.status == "success")
        .count()
    )

    failed = (
        db.query(WorkflowExecution)
        .filter(WorkflowExecution.status == "failed")
        .count()
    )

    running = (
        db.query(WorkflowExecution)
        .filter(WorkflowExecution.status == "running")
        .count()
    )

    return {
        "total_executions": total,
        "successful_executions": successful,
        "failed_executions": failed,
        "running_executions": running,
    }


# --------------------------------------------------
# INDIVIDUAL EXECUTION DETAILS
# --------------------------------------------------

@router.get("/{execution_id}")
def get_execution_by_id(
    execution_id: int,
    db: Session = Depends(get_db),
):
    execution = (
        db.query(WorkflowExecution)
        .filter(WorkflowExecution.id == execution_id)
        .first()
    )

    if not execution:
        raise HTTPException(
            status_code=404,
            detail="Execution not found.",
        )

    return format_execution(execution, db)
