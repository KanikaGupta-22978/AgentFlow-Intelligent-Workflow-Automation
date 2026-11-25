
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.scheduler_service import (
    start_scheduler,
    stop_scheduler,
    schedule_interval_workflow,
    schedule_daily_workflow,
    schedule_weekly_workflow,
    schedule_monthly_workflow,
    schedule_one_time_workflow,
    scheduler,
)


router = APIRouter(
    prefix="/scheduler",
    tags=["Workflow Scheduler"],
)

IST = ZoneInfo("Asia/Kolkata")

SUPPORTED_WORKFLOWS = ["WF001", "WF002", "WF003", "WF004"]


# --------------------------------------------------
# REQUEST MODELS
# Accept both frontend and backend parameter names.
# --------------------------------------------------

class ScheduleRequest(BaseModel):
    workflow_id: str
    minutes: int | None = Field(default=None, gt=0)
    interval_minutes: int | None = Field(default=None, gt=0)


class DailyScheduleRequest(BaseModel):
    workflow_id: str
    time: str | None = None
    hour: int | None = Field(default=None, ge=0, le=23)
    minute: int | None = Field(default=None, ge=0, le=59)


class WeeklyScheduleRequest(BaseModel):
    workflow_id: str
    day: str | None = None
    day_of_week: str | None = None
    time: str | None = None
    hour: int | None = Field(default=None, ge=0, le=23)
    minute: int | None = Field(default=None, ge=0, le=59)


class MonthlyScheduleRequest(BaseModel):
    workflow_id: str
    day: int = Field(ge=1, le=31)
    time: str | None = None
    hour: int | None = Field(default=None, ge=0, le=23)
    minute: int | None = Field(default=None, ge=0, le=59)


class OneTimeScheduleRequest(BaseModel):
    workflow_id: str
    run_date: datetime


# --------------------------------------------------
# VALIDATION HELPERS
# --------------------------------------------------

def validate_workflow(workflow_id: str):
    workflow_id = workflow_id.strip().upper()

    if workflow_id not in SUPPORTED_WORKFLOWS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported workflow ID.",
        )

    return workflow_id


def parse_schedule_time(time_value, hour, minute):
    if time_value:
        try:
            parsed = datetime.strptime(time_value.strip(), "%H:%M")
            return parsed.hour, parsed.minute
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Time must use HH:MM format.",
            )

    if hour is None or minute is None:
        raise HTTPException(
            status_code=400,
            detail="Execution time is required.",
        )

    return hour, minute


# --------------------------------------------------
# START SCHEDULER
# --------------------------------------------------

@router.post("/start")
def start_workflow_scheduler():
    try:
        start_scheduler()

        return {
            "status": "success",
            "message": "Workflow scheduler started.",
            "scheduler_running": scheduler.running,
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# --------------------------------------------------
# STOP SCHEDULER
# --------------------------------------------------

@router.post("/stop")
def stop_workflow_scheduler():
    try:
        if scheduler.running:
            stop_scheduler()

        return {
            "status": "success",
            "message": "Workflow scheduler stopped.",
            "scheduler_running": scheduler.running,
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# --------------------------------------------------
# INTERVAL SCHEDULE
# --------------------------------------------------

@router.post("/schedule")
def create_scheduled_workflow(request: ScheduleRequest):
    workflow_id = validate_workflow(request.workflow_id)
    minutes = request.interval_minutes or request.minutes

    if minutes is None or minutes <= 0:
        raise HTTPException(
            status_code=400,
            detail="A valid interval in minutes is required.",
        )

    try:
        start_scheduler()

        schedule_interval_workflow(workflow_id, minutes)

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "schedule_type": "interval",
            "interval_minutes": minutes,
            "message": "Workflow scheduled successfully.",
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# --------------------------------------------------
# DAILY SCHEDULE
# Supports /daily and /schedule/daily
# --------------------------------------------------

@router.post("/daily")
@router.post("/schedule/daily")
def create_daily_schedule(request: DailyScheduleRequest):
    workflow_id = validate_workflow(request.workflow_id)

    hour, minute = parse_schedule_time(
        request.time,
        request.hour,
        request.minute,
    )

    try:
        start_scheduler()
        schedule_daily_workflow(workflow_id, hour, minute)

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "schedule_type": "daily",
            "time": f"{hour:02d}:{minute:02d}",
            "timezone": "Asia/Kolkata",
            "message": "Daily workflow scheduled successfully.",
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# --------------------------------------------------
# WEEKLY SCHEDULE
# Supports /weekly and /schedule/weekly
# --------------------------------------------------

@router.post("/weekly")
@router.post("/schedule/weekly")
def create_weekly_schedule(request: WeeklyScheduleRequest):
    workflow_id = validate_workflow(request.workflow_id)

    day_of_week = (
        request.day_of_week or request.day or ""
    ).strip().lower()[:3]

    if not day_of_week:
        raise HTTPException(
            status_code=400,
            detail="A weekday is required.",
        )

    hour, minute = parse_schedule_time(
        request.time,
        request.hour,
        request.minute,
    )

    try:
        start_scheduler()

        schedule_weekly_workflow(
            workflow_id,
            day_of_week,
            hour,
            minute,
        )

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "schedule_type": "weekly",
            "day_of_week": day_of_week,
            "time": f"{hour:02d}:{minute:02d}",
            "timezone": "Asia/Kolkata",
            "message": "Weekly workflow scheduled successfully.",
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# --------------------------------------------------
# MONTHLY SCHEDULE
# Supports /monthly and /schedule/monthly
# --------------------------------------------------

@router.post("/monthly")
@router.post("/schedule/monthly")
def create_monthly_schedule(request: MonthlyScheduleRequest):
    workflow_id = validate_workflow(request.workflow_id)

    hour, minute = parse_schedule_time(
        request.time,
        request.hour,
        request.minute,
    )

    try:
        start_scheduler()

        schedule_monthly_workflow(
            workflow_id,
            request.day,
            hour,
            minute,
        )

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "schedule_type": "monthly",
            "day": request.day,
            "time": f"{hour:02d}:{minute:02d}",
            "timezone": "Asia/Kolkata",
            "message": "Monthly workflow scheduled successfully.",
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# --------------------------------------------------
# ONE-TIME SCHEDULE
# Supports /once and /schedule/once
# --------------------------------------------------

@router.post("/once")
@router.post("/schedule/once")
def create_one_time_schedule(request: OneTimeScheduleRequest):
    workflow_id = validate_workflow(request.workflow_id)

    try:
        run_date = request.run_date

        if run_date.tzinfo is None:
            run_date = run_date.replace(tzinfo=IST)

        if run_date <= datetime.now(IST):
            raise HTTPException(
                status_code=400,
                detail="Scheduled date and time must be in the future.",
            )

        start_scheduler()
        schedule_one_time_workflow(workflow_id, run_date)

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "schedule_type": "one_time",
            "run_date": run_date.isoformat(),
            "message": "One-time workflow scheduled successfully.",
        }

    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# --------------------------------------------------
# LIST SCHEDULED JOBS
# --------------------------------------------------

@router.get("/jobs")
def get_scheduled_jobs():
    try:
        scheduled_jobs = []

        for job in scheduler.get_jobs():
            job_id = job.id

            if job_id.endswith("_interval"):
                schedule_type = "interval"
            elif job_id.endswith("_daily"):
                schedule_type = "daily"
            elif job_id.endswith("_weekly"):
                schedule_type = "weekly"
            elif job_id.endswith("_monthly"):
                schedule_type = "monthly"
            elif job_id.endswith("_once"):
                schedule_type = "one_time"
            else:
                schedule_type = "unknown"

            scheduled_jobs.append({
                "id": job.id,
                "job_id": job.id,
                "workflow_id": job.args[0] if job.args else None,
                "schedule_type": schedule_type,
                "trigger": str(job.trigger),
                "next_run_time": (
                    job.next_run_time.isoformat()
                    if job.next_run_time
                    else None
                ),
            })

        return {
            "total_scheduled_jobs": len(scheduled_jobs),
            "running": scheduler.running,
            "scheduler_running": scheduler.running,
            "jobs": scheduled_jobs,
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# --------------------------------------------------
# CANCEL SCHEDULED JOB
# --------------------------------------------------

@router.delete("/jobs/{job_id}")
def delete_scheduled_job(job_id: str):
    try:
        job = scheduler.get_job(job_id)

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Scheduled job not found.",
            )

        scheduler.remove_job(job_id)

        return {
            "status": "success",
            "message": f"Scheduled job {job_id} cancelled successfully.",
            "job_id": job_id,
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
