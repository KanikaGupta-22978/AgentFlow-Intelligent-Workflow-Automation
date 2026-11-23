
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


class ScheduleRequest(BaseModel):
    workflow_id: str
    minutes: int = Field(gt=0)


class DailyScheduleRequest(BaseModel):
    workflow_id: str
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)


class WeeklyScheduleRequest(BaseModel):
    workflow_id: str
    day_of_week: str
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)


class MonthlyScheduleRequest(BaseModel):
    workflow_id: str
    day: int = Field(ge=1, le=31)
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)


class OneTimeScheduleRequest(BaseModel):
    workflow_id: str
    run_date: datetime


def validate_workflow(workflow_id: str):
    if workflow_id not in SUPPORTED_WORKFLOWS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported workflow ID.",
        )


@router.post("/start")
def start_workflow_scheduler():
    start_scheduler()

    return {
        "status": "success",
        "message": "Workflow scheduler started.",
    }


@router.post("/stop")
def stop_workflow_scheduler():
    if scheduler.running:
        stop_scheduler()

        return {
            "status": "success",
            "message": "Workflow scheduler stopped.",
        }

    return {
        "status": "info",
        "message": "Workflow scheduler is not running.",
    }


@router.post("/schedule")
def create_scheduled_workflow(request: ScheduleRequest):
    validate_workflow(request.workflow_id)

    try:
        schedule_interval_workflow(
            workflow_id=request.workflow_id,
            minutes=request.minutes,
        )

        return {
            "status": "success",
            "workflow_id": request.workflow_id,
            "schedule_type": "interval",
            "interval_minutes": request.minutes,
            "message": "Workflow scheduled successfully.",
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/schedule/daily")
def create_daily_schedule(request: DailyScheduleRequest):
    validate_workflow(request.workflow_id)

    try:
        schedule_daily_workflow(
            request.workflow_id,
            request.hour,
            request.minute,
        )

        return {
            "status": "success",
            "workflow_id": request.workflow_id,
            "schedule_type": "daily",
            "time": f"{request.hour:02d}:{request.minute:02d}",
            "timezone": "Asia/Kolkata",
            "message": "Daily workflow scheduled successfully.",
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/schedule/weekly")
def create_weekly_schedule(request: WeeklyScheduleRequest):
    validate_workflow(request.workflow_id)

    try:
        schedule_weekly_workflow(
            request.workflow_id,
            request.day_of_week,
            request.hour,
            request.minute,
        )

        return {
            "status": "success",
            "workflow_id": request.workflow_id,
            "schedule_type": "weekly",
            "day_of_week": request.day_of_week,
            "time": f"{request.hour:02d}:{request.minute:02d}",
            "timezone": "Asia/Kolkata",
            "message": "Weekly workflow scheduled successfully.",
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/schedule/monthly")
def create_monthly_schedule(request: MonthlyScheduleRequest):
    validate_workflow(request.workflow_id)

    try:
        schedule_monthly_workflow(
            request.workflow_id,
            request.day,
            request.hour,
            request.minute,
        )

        return {
            "status": "success",
            "workflow_id": request.workflow_id,
            "schedule_type": "monthly",
            "day": request.day,
            "time": f"{request.hour:02d}:{request.minute:02d}",
            "timezone": "Asia/Kolkata",
            "message": "Monthly workflow scheduled successfully.",
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/schedule/once")
def create_one_time_schedule(request: OneTimeScheduleRequest):
    validate_workflow(request.workflow_id)

    try:
        run_date = request.run_date

        if run_date.tzinfo is None:
            run_date = run_date.replace(tzinfo=IST)

        schedule_one_time_workflow(
            request.workflow_id,
            run_date,
        )

        return {
            "status": "success",
            "workflow_id": request.workflow_id,
            "schedule_type": "one_time",
            "run_date": run_date.isoformat(),
            "message": "One-time workflow scheduled successfully.",
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


# List all scheduled workflows
@router.get("/jobs")
def get_scheduled_jobs():
    jobs = scheduler.get_jobs()

    scheduled_jobs = []

    for job in jobs:
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
            "job_id": job.id,
            "workflow_id": (
                job.args[0] if job.args else None
            ),
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
        "scheduler_running": scheduler.running,
        "jobs": scheduled_jobs,
    }
