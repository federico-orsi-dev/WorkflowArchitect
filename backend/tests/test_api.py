from __future__ import annotations

import json
from collections.abc import Iterator
from unittest.mock import patch

import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient


def _mock_llm_response(prompt: str, _timeout_seconds: int) -> str:
    if "User goal:" in prompt:
        return json.dumps(
            {
                "tasks": [
                    {
                        "id": "t1",
                        "title": "Define implementation plan",
                        "details": "Break the feature into small executable steps.",
                        "estimate_minutes": 30,
                        "risk": "low",
                        "definition_of_done": [
                            "Plan documented",
                            "Dependencies identified",
                        ],
                    }
                ],
                "total_estimate_minutes": 30,
                "notes": "Mocked planning response.",
            }
        )

    if "Change summary:" in prompt:
        return json.dumps(
            {
                "commit_message": "feat(api): mock implementation",
                "pr_title": "Add mocked API implementation",
                "pr_body_markdown": (
                    "### Why\nKeep tests isolated from external LLM calls.\n\n"
                    "### What\nAdd mocked responses for commit generation.\n\n"
                    "### How to test\n- Run the API test suite"
                ),
                "changelog_entry": "Changed: mocked commit generation in API tests.",
                "labels": ["chore", "tests"],
            }
        )

    if "This pull request contains the following commits:" in prompt:
        return json.dumps(
            {
                "pr_title": "Aggregate mocked changes",
                "pr_body_markdown": (
                    "### Why\nKeep CI deterministic.\n\n"
                    "### What\nAggregate mocked commit outputs for tests.\n\n"
                    "### How to test\n- Run the API test suite"
                ),
                "changelog_entry": "Changed: mocked PR aggregation in tests.",
                "labels": ["tests", "api"],
            }
        )

    raise AssertionError(f"Unexpected LLM prompt: {prompt}")


@pytest.fixture(autouse=True)
def mock_llm_invoke() -> Iterator[None]:
    with patch("app.llm.client_factory.LlmClient.invoke", side_effect=_mock_llm_response):
        yield


@pytest.mark.asyncio
async def test_plan_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/plan", json={"prompt": "Ship a small feature"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "PLAN"
    assert payload["input"] == "Ship a small feature"
    assert isinstance(payload["result"], dict)
    assert "tasks" in payload["result"]
    assert payload["result"]["tasks"][0]["title"] == "Define implementation plan"


@pytest.mark.asyncio
async def test_commit_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/commit", json={"message": "Update README"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "COMMIT"
    assert payload["input"] == "Update README"
    assert isinstance(payload["result"], dict)
    assert payload["result"]["commit_message"] == "feat(api): mock implementation"
    assert payload["result"]["labels"] == ["chore", "tests"]


@pytest.mark.asyncio
async def test_pr_endpoint() -> None:
    transport = ASGITransport(app=app)
    commits = [
        {
            "commit_message": "feat(api): add operations endpoint",
            "labels": ["feat", "api"],
        }
    ]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/pr", json={"commits": commits})
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "PR"
    assert isinstance(payload["input"], list)
    assert isinstance(payload["result"], dict)
    assert payload["result"]["pr_title"] == "Aggregate mocked changes"
