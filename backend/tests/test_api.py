import httpx

from app.main import app


def test_plan_endpoint() -> None:
    transport = httpx.ASGITransport(app=app)
    with httpx.Client(transport=transport, base_url="http://test") as client:
        response = client.post("/api/plan", json={"prompt": "Ship a small feature"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "PLAN"
    assert payload["input"] == "Ship a small feature"
    assert isinstance(payload["result"], dict)
    assert "tasks" in payload["result"]


def test_commit_endpoint() -> None:
    transport = httpx.ASGITransport(app=app)
    with httpx.Client(transport=transport, base_url="http://test") as client:
        response = client.post("/api/commit", json={"message": "Update README"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "COMMIT"
    assert payload["input"] == "Update README"
    assert isinstance(payload["result"], dict)
    assert "commit_message" in payload["result"]
    assert "labels" in payload["result"]


def test_pr_endpoint() -> None:
    transport = httpx.ASGITransport(app=app)
    commits = [
        {
            "commit_message": "feat(api): add operations endpoint",
            "labels": ["feat", "api"],
        }
    ]
    with httpx.Client(transport=transport, base_url="http://test") as client:
        response = client.post("/api/pr", json={"commits": commits})
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "PR"
    assert isinstance(payload["input"], list)
    assert isinstance(payload["result"], dict)
    assert "pr_title" in payload["result"]
