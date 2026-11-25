
from app.services import execution_service


def _record(zone="Shivamogga Zone", uptime=100, score=80, timestamp=None):
    return {
        "site_zone": zone,
        "site_code": "SITE-001",
        "link": "LINK-001",
        "IP": "10.0.0.1",
        "isp": "Example ISP",
        "link_type": "MPLS",
        "uptime": uptime,
        "performance_score": score,
        "avg_latency": 10,
        "avg_packet_drop": 0,
        "avg_jitter": 1,
        "avg_cpu": 20,
        "avg_memory": 30,
        "circuit_id": "CIRCUIT-001",
        "site_address": "Example address",
        "timestamp": timestamp,
    }


def _stub_data(
    monkeypatch,
    records,
    start="2026-11-02T04:30:00",
    end="2026-11-02T12:30:00",
):
    monkeypatch.setattr(
        execution_service,
        "load_performance_stats",
        lambda: records,
    )
    monkeypatch.setattr(
        execution_service,
        "load_performance_metadata",
        lambda: {
            "report_id": "test-report",
            "report_date": {"start": start, "end": end},
        },
    )


def test_wf004_filters_by_zone_and_lists_zero_uptime_links(monkeypatch):
    _stub_data(
        monkeypatch,
        [
            _record(uptime=0, score=0),
            _record(uptime=100, score=80),
            _record(zone="Mumbai Zone", uptime=0, score=0),
        ],
    )

    result = execution_service.execute_performance_report(
        {"zone": "shivamogga zone"}
    )

    assert result["total_records"] == 2
    assert result["down_link_count"] == 1
    assert result["down_links"][0]["site_code"] == "SITE-001"
    assert result["average_performance_score"] == 40
    assert result["time_filter_applied"] is False


def test_wf004_excludes_undated_and_out_of_period_records(monkeypatch):
    _stub_data(
        monkeypatch,
        [
            _record(
                uptime=0,
                score=0,
                timestamp="2026-11-02T06:00:00",
            ),
            _record(
                uptime=100,
                score=90,
                timestamp="2026-11-02T03:00:00",
            ),
            _record(
                uptime=0,
                score=0,
                timestamp=None,
            ),
        ],
    )

    result = execution_service.execute_performance_report(
        {"zone": "Shivamogga Zone", "hours": 7}
    )

    assert result["total_records"] == 1
    assert result["down_link_count"] == 1
    assert len(result["down_links"]) == 1
    assert result["time_filter_applied"] is True
    assert result["reporting_period"] == {
        "start": "2026-11-02T05:30:00",
        "end": "2026-11-02T12:30:00",
    }
    assert "without timestamps" in result["time_filter_note"]
    assert "invalid timestamps" in result["time_filter_note"]


def test_wf004_applies_full_time_filter_when_all_records_are_dated(monkeypatch):
    _stub_data(
        monkeypatch,
        [
            _record(
                uptime=0,
                score=0,
                timestamp="2026-11-02T06:00:00",
            ),
            _record(
                uptime=100,
                score=90,
                timestamp="2026-11-02T03:00:00",
            ),
            _record(
                uptime=100,
                score=70,
                timestamp="2026-11-02T10:00:00",
            ),
        ],
    )

    result = execution_service.execute_performance_report(
        {"zone": "Shivamogga Zone", "hours": 7}
    )

    assert result["total_records"] == 2
    assert result["down_link_count"] == 1
    assert result["time_filter_applied"] is True
    assert result["time_filter_note"] == (
        "Report includes only records with valid timestamps between "
        "2026-11-02T05:30:00 and 2026-11-02T12:30:00. "
        "Records without timestamps or with invalid timestamps were excluded."
    )
    assert result["average_performance_score"] == 35


def test_wf004_returns_consistent_empty_result_for_unknown_zone(monkeypatch):
    _stub_data(monkeypatch, [_record()])

    result = execution_service.execute_performance_report(
        {"zone": "Unknown Zone", "hours": 7}
    )

    assert result["total_records"] == 0
    assert result["down_link_count"] == 0
    assert result["down_links"] == []
    assert result["records"] == []
    assert result["time_filter_applied"] is True
