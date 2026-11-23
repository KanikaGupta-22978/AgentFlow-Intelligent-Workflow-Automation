
from unittest.mock import Mock, patch

from app.services import scheduler_service


def test_scheduler_starts_and_stops():
    with patch.object(
        scheduler_service,
        "scheduler",
        new=Mock(running=False),
    ) as mock_scheduler:

        scheduler_service.start_scheduler()
        mock_scheduler.start.assert_called_once()

        mock_scheduler.running = True
        scheduler_service.stop_scheduler()

        mock_scheduler.shutdown.assert_called_once_with(wait=False)


def test_interval_workflow_is_scheduled():
    with patch.object(
        scheduler_service.scheduler,
        "add_job"
    ) as add_job_mock:

        scheduler_service.schedule_interval_workflow(
            workflow_id="WF001",
            minutes=1,
        )

        add_job_mock.assert_called_once()
        _, kwargs = add_job_mock.call_args

        assert kwargs["id"] == "WF001_interval"
        assert kwargs["minutes"] == 1
        assert kwargs["args"] == ["WF001"]


def test_interval_rejects_zero_minutes():
    try:
        scheduler_service.schedule_interval_workflow("WF001", 0)
        assert False, "Expected ValueError"
    except ValueError as error:
        assert "greater than zero" in str(error)
