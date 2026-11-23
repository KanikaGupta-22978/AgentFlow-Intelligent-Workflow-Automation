
from app.agents import langgraph_agent


def test_gemini_failure_uses_rule_based_fallback(monkeypatch):
    def mock_gemini(_instruction):
        raise RuntimeError("Gemini API unavailable")

    def mock_select_workflow(_instruction):
        return "WF004"

    monkeypatch.setattr(
        langgraph_agent,
        "understand_instruction",
        mock_gemini,
    )
    monkeypatch.setattr(
        langgraph_agent,
        "select_workflow",
        mock_select_workflow,
    )

    state = {
        "user_instruction": "Generate a performance report",
        "workflow_id": "",
        "parameters": {},
        "llm_parameters": {},
        "status": "started",
        "error": "",
        "execution_result": {},
        "llm_used": False,
        "llm_warning": "",
    }

    result = langgraph_agent.workflow_selection_node(state)

    assert result["workflow_id"] == "WF004"
    assert result["status"] == "workflow_selected"
    assert result["llm_used"] is False
    assert "Gemini unavailable" in result["llm_warning"]


def test_gemini_success_selects_workflow(monkeypatch):
    def mock_gemini(_instruction):
        return {
            "workflow_id": "WF004",
            "parameters": {"hours": 6},
        }

    monkeypatch.setattr(
        langgraph_agent,
        "understand_instruction",
        mock_gemini,
    )

    state = {
        "user_instruction": "Generate a performance report",
        "workflow_id": "",
        "parameters": {},
        "llm_parameters": {},
        "status": "started",
        "error": "",
        "execution_result": {},
        "llm_used": False,
        "llm_warning": "",
    }

    result = langgraph_agent.workflow_selection_node(state)

    assert result["workflow_id"] == "WF004"
    assert result["llm_parameters"] == {"hours": 6}
    assert result["status"] == "workflow_selected"
    assert result["llm_used"] is True
