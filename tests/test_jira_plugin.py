
from types import SimpleNamespace
from urllib.error import URLError

from app.plugins.jira_plugin import JiraPlugin


def make_plugin(monkeypatch):
    # Provide a lightweight database mock with rollback support.
    fake_db = SimpleNamespace(
        rollback=lambda: None
    )

    plugin = JiraPlugin(db=fake_db)

    monkeypatch.setattr(
        plugin,
        "_get_configuration",
        lambda: (
            "https://example.atlassian.net",
            "KAN",
            {"Authorization": "Basic test"},
        ),
    )

    return plugin


def test_existing_jira_issue_is_not_created_again(monkeypatch):
    plugin = make_plugin(monkeypatch)

    monkeypatch.setattr(
        plugin,
        "_find_existing_jira_issue",
        lambda **kwargs: {
            "jira_issue_key": "KAN-100",
            "jira_issue_id": "10000",
            "status": "Open",
        },
    )

    monkeypatch.setattr(
        plugin,
        "_save_local_ticket",
        lambda **kwargs: SimpleNamespace(id=10),
    )

    def should_not_create(*args, **kwargs):
        raise AssertionError("A duplicate Jira issue must not be created.")

    monkeypatch.setattr(
        "app.plugins.jira_plugin.urllib.request.urlopen",
        should_not_create,
    )

    result = plugin.execute({
        "title": "Network Alert - High Latency",
        "description": "High latency detected.",
    })

    assert result["success"] is True
    assert result["duplicate"] is True
    assert result["jira_issue_key"] == "KAN-100"
    assert "No new ticket was created" in result["message"]


def test_new_jira_issue_is_created_when_no_duplicate_exists(monkeypatch):
    plugin = make_plugin(monkeypatch)

    monkeypatch.setattr(
        plugin,
        "_find_existing_jira_issue",
        lambda **kwargs: None,
    )

    monkeypatch.setattr(
        plugin,
        "_find_existing_local_ticket",
        lambda *args, **kwargs: None,
    )

    monkeypatch.setattr(
        plugin,
        "_save_local_ticket",
        lambda **kwargs: SimpleNamespace(id=20),
    )

    calls = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"id": "20000", "key": "KAN-200"}'

    def fake_urlopen(request, timeout=30):
        calls.append(request)
        return FakeResponse()

    monkeypatch.setattr(
        "app.plugins.jira_plugin.urllib.request.urlopen",
        fake_urlopen,
    )

    result = plugin.execute({
        "title": "Network Alert - High Latency",
        "description": "A new high latency incident.",
    })

    assert result["success"] is True
    assert result["duplicate"] is False
    assert result["jira_issue_key"] == "KAN-200"
    assert len(calls) == 1
    assert calls[0].get_method() == "POST"


def test_jira_search_failure_does_not_create_ticket(monkeypatch):
    plugin = make_plugin(monkeypatch)

    def failed_search(**kwargs):
        raise URLError("Jira search unavailable")

    monkeypatch.setattr(
        plugin,
        "_find_existing_jira_issue",
        failed_search,
    )

    def should_not_create(*args, **kwargs):
        raise AssertionError(
            "Jira creation must not happen when duplicate search fails."
        )

    monkeypatch.setattr(
        "app.plugins.jira_plugin.urllib.request.urlopen",
        should_not_create,
    )

    result = plugin.execute({
        "title": "Network Alert - High Latency",
        "description": "High latency detected.",
    })

    assert result["success"] is False
    assert result["duplicate"] is False
    assert "Could not connect to Jira" in result["message"]
