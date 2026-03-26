import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient


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
    assert "commit_message" in payload["result"]
    assert "labels" in payload["result"]


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
    assert "pr_title" in payload["result"]
