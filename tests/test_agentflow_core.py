
import pytest

from app.services.data_service import (
    load_alerts,
    load_performance_stats,
    get_available_zones,
    get_performance_by_zone,
)
from app.agents.workflow_selection_agent import (
    select_workflow,
    extract_parameters,
    validate_parameters,
)
from app.agents.plugin_selection_agent import select_plugin
from app.plugins.email_plugin import EmailPlugin
from app.agents.reporting_agent import generate_report


# DATA SERVICE TESTS

def test_alert_data_loads():
    alerts = load_alerts()
    assert isinstance(alerts, list)
    assert len(alerts) > 0


def test_performance_data_loads():
    records = load_performance_stats()
    assert isinstance(records, list)
    assert len(records) > 0


def test_available_zones():
    zones = get_available_zones()
    assert isinstance(zones, list)
    assert len(zones) > 0


def test_shivamogga_performance_data():
    records = get_performance_by_zone("Shivamogga Zone")
    assert len(records) > 0
    assert all(
        record.get("site_zone", "").casefold() == "shivamogga zone"
        for record in records
    )


# WORKFLOW SELECTION TESTS

@pytest.mark.parametrize(
    "instruction, expected",
    [
        ("Show me the latest alerts", "WF001"),
        ("Create a Jira ticket", "WF002"),
        ("Send an email notification", "WF003"),
        ("Generate a performance report", "WF004"),
    ],
)
def test_workflow_selection(instruction, expected):
    assert select_workflow(instruction) == expected


def test_empty_instruction_rejected():
    with pytest.raises(ValueError):
        select_workflow("")


def test_unknown_instruction_rejected():
    with pytest.raises(ValueError):
        select_workflow("Do something unrelated")


# PARAMETER EXTRACTION TESTS

def test_performance_parameter_extraction():
    result = extract_parameters(
        "WF004",
        "Generate performance report for Shivamogga Zone for the last 6 hours",
    )

    assert result["zone"] == "Shivamogga Zone"
    assert result["hours"] == 6


def test_performance_parameter_validation():
    result = validate_parameters(
        "WF004",
        {"zone": "Shivamogga Zone", "hours": 6},
    )

    assert result["hours"] == 6


def test_invalid_performance_duration():
    with pytest.raises(ValueError):
        validate_parameters("WF004", {"hours": 0})


# PLUGIN SELECTION TESTS

@pytest.mark.parametrize(
    "workflow_id, expected",
    [
        ("WF001", None),
        ("WF002", "jira"),
        ("WF003", "email"),
        ("WF004", None),
    ],
)
def test_plugin_selection(workflow_id, expected):
    assert select_plugin(workflow_id) == expected


def test_unknown_plugin_workflow_rejected():
    with pytest.raises(ValueError):
        select_plugin("WF999")


# EMAIL PLUGIN TESTS

def test_email_plugin_success():
    plugin = EmailPlugin()

    result = plugin.execute({
        "recipient": "admin@example.com",
        "subject": "Test notification",
        "message": "This is a test message.",
    })

    assert result["success"] is True
    assert result["plugin"] == "email"
    assert result["recipient"] == "admin@example.com"


def test_email_plugin_missing_recipient():
    plugin = EmailPlugin()

    with pytest.raises(ValueError):
        plugin.execute({
            "message": "Test message",
        })


def test_email_plugin_missing_message():
    plugin = EmailPlugin()

    with pytest.raises(ValueError):
        plugin.execute({
            "recipient": "admin@example.com",
        })


# REPORTING AGENT TESTS

def test_reporting_agent():
    result = generate_report({
        "workflow_name": "Daily Alert Summary",
        "total_alerts": 10,
        "unresolved_alerts": [
            {
                "device/link": "Device 1",
                "intensity": "HIGH",
                "ip_address": "10.0.0.1",
            }
        ],
    })

    assert result["workflow_name"] == "Daily Alert Summary"
    assert result["total_alerts"] == 10
    assert result["unresolved_alert_count"] == 1
    assert "1 unresolved alerts" in result["summary"]
