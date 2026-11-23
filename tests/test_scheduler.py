
import time

from app.services.scheduler_service import (
    start_scheduler,
    stop_scheduler,
    schedule_interval_workflow,
)


def main():
    try:
        start_scheduler()

        # Run WF001 every 1 minute
        schedule_interval_workflow(
            workflow_id="WF001",
            minutes=1,
        )

        print("\nScheduler demonstration started.")
        print("Waiting for the scheduled workflow...")

        # Keep running long enough for the first trigger
        time.sleep(70)

    finally:
        stop_scheduler()


if __name__ == "__main__":
    main()
