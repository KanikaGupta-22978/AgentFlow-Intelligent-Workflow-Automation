
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from app.services.execution_service import execute_workflow


IST = ZoneInfo("Asia/Kolkata")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "data" / "agentic_workflow.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

scheduler = BackgroundScheduler(
    timezone=IST,
    jobstores={
        "default": SQLAlchemyJobStore(url=DATABASE_URL)
    },
)


def run_scheduled_workflow(workflow_id: str):
    """Execute a workflow through the scheduler."""
    print(f"\nScheduled workflow started: {workflow_id}")

    try:
        result = execute_workflow(workflow_id)
        print("Scheduled workflow completed successfully.")
        print("Result:", result)
    except Exception as error:
        print("Scheduled workflow failed:", str(error))


def start_scheduler():
    """Start the background scheduler and restore saved jobs."""
    if not scheduler.running:
        scheduler.start()
        print("Workflow scheduler started.")


def stop_scheduler():
    """Stop the background scheduler without deleting saved jobs."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("Workflow scheduler stopped.")


def schedule_interval_workflow(workflow_id: str, minutes: int):
    """Schedule a workflow at regular intervals."""
    if minutes <= 0:
        raise ValueError("Interval must be greater than zero.")

    scheduler.add_job(
        run_scheduled_workflow,
        trigger="interval",
        minutes=minutes,
        args=[workflow_id],
        id=f"{workflow_id}_interval",
        replace_existing=True,
    )

    print(f"Workflow {workflow_id} scheduled every {minutes} minutes.")


def schedule_daily_workflow(workflow_id: str, hour: int, minute: int):
    """Schedule a workflow daily at the specified IST time."""
    validate_time(hour, minute)

    scheduler.add_job(
        run_scheduled_workflow,
        trigger="cron",
        hour=hour,
        minute=minute,
        timezone=IST,
        args=[workflow_id],
        id=f"{workflow_id}_daily",
        replace_existing=True,
    )

    print(
        f"Workflow {workflow_id} scheduled daily "
        f"at {hour:02d}:{minute:02d} IST."
    )


def schedule_weekly_workflow(
    workflow_id: str,
    day_of_week: str,
    hour: int,
    minute: int,
):
    """Schedule a workflow weekly at the specified IST time."""
    validate_time(hour, minute)

    valid_days = [
        "mon", "tue", "wed", "thu", "fri", "sat", "sun",
    ]

    day_of_week = day_of_week.strip().lower()[:3]

    if day_of_week not in valid_days:
        raise ValueError(
            "Invalid day. Use mon, tue, wed, thu, fri, sat, or sun."
        )

    scheduler.add_job(
        run_scheduled_workflow,
        trigger="cron",
        day_of_week=day_of_week,
        hour=hour,
        minute=minute,
        timezone=IST,
        args=[workflow_id],
        id=f"{workflow_id}_weekly",
        replace_existing=True,
    )

    print(
        f"Workflow {workflow_id} scheduled weekly on "
        f"{day_of_week} at {hour:02d}:{minute:02d} IST."
    )


def schedule_monthly_workflow(
    workflow_id: str,
    day: int,
    hour: int,
    minute: int,
):
    """Schedule a workflow monthly at the specified IST time."""
    validate_time(hour, minute)

    if day < 1 or day > 31:
        raise ValueError("Day must be between 1 and 31.")

    scheduler.add_job(
        run_scheduled_workflow,
        trigger="cron",
        day=day,
        hour=hour,
        minute=minute,
        timezone=IST,
        args=[workflow_id],
        id=f"{workflow_id}_monthly",
        replace_existing=True,
    )

    print(
        f"Workflow {workflow_id} scheduled monthly on day "
        f"{day} at {hour:02d}:{minute:02d} IST."
    )


def schedule_one_time_workflow(workflow_id: str, run_date: datetime):
    """Schedule a workflow once at an IST date and time."""
    if run_date.tzinfo is None:
        run_date = run_date.replace(tzinfo=IST)
    else:
        run_date = run_date.astimezone(IST)

    if run_date <= datetime.now(IST):
        raise ValueError("Scheduled date and time must be in the future.")

    scheduler.add_job(
        run_scheduled_workflow,
        trigger="date",
        run_date=run_date,
        timezone=IST,
        args=[workflow_id],
        id=f"{workflow_id}_once",
        replace_existing=True,
    )

    print(
        f"Workflow {workflow_id} scheduled once for "
        f"{run_date.isoformat()}."
    )


def validate_time(hour: int, minute: int):
    """Validate 24-hour clock time."""
    if hour < 0 or hour > 23:
        raise ValueError("Hour must be between 0 and 23.")

    if minute < 0 or minute > 59:
        raise ValueError("Minute must be between 0 and 59.")
