
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


# -----------------------------
# REQUEST MODELS
# -----------------------------

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


# -----------------------------
# WORKFLOW VALIDATION
# -----------------------------

def validate_workflow(workflow_id: str):
    workflow_id = workflow_id.strip().upper()

    if workflow_id not in SUPPORTED_WORKFLOWS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported workflow ID.",
        )

    return workflow_id


# -----------------------------
# START SCHEDULER
# -----------------------------

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


# -----------------------------
# STOP SCHEDULER
# -----------------------------

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

        return {
            "status": "info",
            "message": "Workflow scheduler is not running.",
            "scheduler_running": False,
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# -----------------------------
# INTERVAL SCHEDULE
# -----------------------------

@router.post("/schedule")
def create_scheduled_workflow(request: ScheduleRequest):
    workflow_id = validate_workflow(request.workflow_id)

    try:
        schedule_interval_workflow(
            workflow_id=workflow_id,
            minutes=request.minutes,
        )

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "schedule_type": "interval",
            "interval_minutes": request.minutes,
            "message": "Workflow scheduled successfully.",
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# -----------------------------
# DAILY SCHEDULE
# -----------------------------

@router.post("/schedule/daily")
def create_daily_schedule(request: DailyScheduleRequest):
    workflow_id = validate_workflow(request.workflow_id)

    try:
        schedule_daily_workflow(
            workflow_id,
            request.hour,
            request.minute,
        )

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "schedule_type": "daily",
            "time": f"{request.hour:02d}:{request.minute:02d}",
            "timezone": "Asia/Kolkata",
            "message": "Daily workflow scheduled successfully.",
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# -----------------------------
# WEEKLY SCHEDULE
# -----------------------------

@router.post("/schedule/weekly")
def create_weekly_schedule(request: WeeklyScheduleRequest):
    workflow_id = validate_workflow(request.workflow_id)

    try:
        day_of_week = request.day_of_week.strip().lower()

        schedule_weekly_workflow(
            workflow_id,
            day_of_week,
            request.hour,
            request.minute,
        )

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "schedule_type": "weekly",
            "day_of_week": day_of_week,
            "time": f"{request.hour:02d}:{request.minute:02d}",
            "timezone": "Asia/Kolkata",
            "message": "Weekly workflow scheduled successfully.",
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# -----------------------------
# MONTHLY SCHEDULE
# -----------------------------

@router.post("/schedule/monthly")
def create_monthly_schedule(request: MonthlyScheduleRequest):
    workflow_id = validate_workflow(request.workflow_id)

    try:
        schedule_monthly_workflow(
            workflow_id,
            request.day,
            request.hour,
            request.minute,
        )

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "schedule_type": "monthly",
            "day": request.day,
            "time": f"{request.hour:02d}:{request.minute:02d}",
            "timezone": "Asia/Kolkata",
            "message": "Monthly workflow scheduled successfully.",
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# -----------------------------
# ONE-TIME SCHEDULE
# -----------------------------

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

        schedule_one_time_workflow(
            workflow_id,
            run_date,
        )

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


# -----------------------------
# LIST SCHEDULED WORKFLOWS
# -----------------------------

@router.get("/jobs")
def get_scheduled_jobs():
    try:
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

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# -----------------------------
# CANCEL / DELETE SCHEDULED JOB
# -----------------------------

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
