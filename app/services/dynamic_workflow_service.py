
from sqlalchemy.orm import Session

from app.database.models import Workflow
from app.schemas.dynamic_workflow import DynamicWorkflowCreate


def create_dynamic_workflow(
    db: Session,
    workflow_data: DynamicWorkflowCreate,
):
    """Save a dynamically generated workflow in the database."""

    workflow = Workflow(
        name=workflow_data.name,
        description=workflow_data.description,
        workflow_type="dynamic",
        definition={
            "trigger": workflow_data.trigger,
            "steps": [
                step.model_dump()
                for step in workflow_data.steps
            ],
        },
        is_active=True,
    )

    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    return workflow


def get_dynamic_workflows(db: Session):
    """Retrieve all dynamically generated workflows."""

    return (
        db.query(Workflow)
        .filter(Workflow.workflow_type == "dynamic")
        .all()
    )


def get_dynamic_workflow_by_id(
    db: Session,
    workflow_id: int,
):
    """Retrieve a dynamic workflow by database ID."""

    return (
        db.query(Workflow)
        .filter(
            Workflow.id == workflow_id,
            Workflow.workflow_type == "dynamic",
        )
        .first()
    )
