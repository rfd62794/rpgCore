import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from src.tools.apj.agents.model_router import ModelRouter, AccountRateLimitState, BudgetState, RoutingDecision
from src.tools.apj.agents.base_agent import AgentConfig

@pytest.fixture
def mock_config():
    return AgentConfig.model_validate({
        "name": "test_agent",
        "role": "tester",
        "department": "analysis",
        "model_preference": "local",
        "prompts": {"system": "s.md", "fewshot": "f.md"},
        "schema": "CoherenceReport",
        "fallback": {"session_primer": "fail", "open_risks": [], "queued_focus": "none", "constitutional_flags": [], "corpus_hash": ""},
        "save_output": False,
        "log_quality": False
    })

def test_router_local_department_routes_local(mock_config):
    assert ModelRouter._decide(mock_config) == RoutingDecision.LOCAL

def test_router_execution_department_routes_remote(mock_config):
    mock_config.department = "execution"
    assert ModelRouter._decide(mock_config) == RoutingDecision.REMOTE

def test_router_account_daily_limit_blocks_all_remote():
    state = AccountRateLimitState(requests_today=50, daily_limit=50)
    can, reason = state.can_request()
    assert can is False
    assert "daily limit" in reason

def test_router_account_rpm_limit_blocks_all_remote():
    state = AccountRateLimitState(requests_this_minute=20, rpm_limit=20)
    can, reason = state.can_request()
    # If minute reset hasn't happened
    assert can is False
    assert "RPM limit" in reason

def test_router_budget_hard_stop():
    budget = BudgetState(session_tokens_used=9500, session_hard_limit=10000)
    assert budget.check(600) == "hard_stop"
    assert budget.check(400) == "ok"

def test_router_budget_warn():
    budget = BudgetState(daily_tokens_used=19500, daily_soft_limit=20000)
    assert budget.check(600) == "warn"

@patch("src.tools.apj.agents.model_router.get_ollama_model")
@patch("pydantic_ai.Agent.run", new_callable=MagicMock)
def test_router_tries_local_success(mock_agent_run, mock_get_ollama, mock_config):
    mock_get_ollama.return_value = MagicMock()
    # To support asyncio.run(agent.run(prompt)), the mock must return a coroutine-like object
    # or just use a helper to make it awaitable.
    import asyncio
    future = asyncio.Future()
    future.set_result(MagicMock(output='{"test": "ok"}'))
    mock_agent_run.return_value = future
    
    res = ModelRouter._try_local("prompt")
    assert res == '{"test": "ok"}'

def test_handle_429_provider_saturated():
    err = Exception("Provider overloaded")
    assert ModelRouter._handle_429(err, "model") == "provider_saturated"

def test_handle_429_account_limited():
    err = Exception("Rate limit exceeded 429")
    assert ModelRouter._handle_429(err, "model") == "account_rate_limited"
