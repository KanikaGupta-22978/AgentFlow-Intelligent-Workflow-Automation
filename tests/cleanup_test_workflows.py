
from app.database.connection import SessionLocal
from app.database.models import Workflow


def cleanup():
    db = SessionLocal()

    try:
        deleted = (
            db.query(Workflow)
            .filter(Workflow.id.in_([1, 2]))
            .delete(synchronize_session=False)
        )

        db.commit()
        print(f"Deleted {deleted} test workflow records.")

    finally:
        db.close()


if __name__ == "__main__":
    cleanup()
