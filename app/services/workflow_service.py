
from sqlalchemy.orm import Session

from app.database.models import Workflow
from app.schemas.workflow import WorkflowCreate


def create_workflow(db: Session, workflow_data: WorkflowCreate):
    workflow = Workflow(
        name=workflow_data.name,
        description=workflow_data.description,
        workflow_type=workflow_data.workflow_type,
        definition=workflow_data.definition,
    )

    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    return workflow


def get_all_workflows(db: Session):
    return db.query(Workflow).all()


def get_workflow_by_id(db: Session, workflow_id: int):
    return db.query(Workflow).filter(
        Workflow.id == workflow_id
    ).first()
