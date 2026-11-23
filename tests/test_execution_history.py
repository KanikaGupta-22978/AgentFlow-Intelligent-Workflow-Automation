from app.database.connection import SessionLocal
from app.database.models import WorkflowExecution


def main():
    db = SessionLocal()

    try:
        executions = (
            db.query(WorkflowExecution)
            .order_by(WorkflowExecution.id.desc())
            .all()
        )

        print("TOTAL EXECUTIONS:", len(executions))

        for execution in executions:
            print("\nExecution ID:", execution.id)
            print("Status:", execution.status)
            print("Input:", execution.input_data)
            print("Output saved:", execution.output_data is not None)
            print("Error:", execution.error_message)

    finally:
        db.close()


if __name__ == "__main__":
    main()