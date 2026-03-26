from __future__ import annotations

import json

from app.core.settings import settings
from app.llm.client_factory import create_client
from app.llm.json_guard import parse_json_strict
from app.llm.prompts import COMMIT_SYSTEM_PROMPT
from app.llm.tracing import get_tracer
from app.schemas.commit import CommitResult


class CommitService:
    def __init__(self) -> None:
        self.client = create_client(settings)

    def run(
        self,
        message: str,
        plan_id: str | None = None,
        task_id: str | None = None,
    ) -> CommitResult:
        if not self.client:
            result = CommitResult(
                commit_message="chore: add placeholder message",
                pr_title="CommitSense fallback",
                pr_body_markdown=(
                    "### Why\nNo client configured.\n\n### What\nN/A\n\n### How to test\nN/A"
                ),
                changelog_entry="Changed: placeholder commit response.",
                labels=["chore"],
            )
            if plan_id or task_id:
                return result.model_copy(
                    update={"plan_id": plan_id, "task_id": task_id},
                )
            return result

        schema_hint = json.dumps(
            {
                "commit_message": "feat(scope): ...",
                "pr_title": "...",
                "pr_body_markdown": "### Why...### What...### How to test...",
                "changelog_entry": "Changed: ...",
                "labels": ["refactor", "tests"],
            },
            indent=2,
        )

        user_prompt = f"Change summary: {message}\n\nSchema:\n{schema_hint}"
        full_prompt = f"{COMMIT_SYSTEM_PROMPT}\n\n{user_prompt}"
        tracer = get_tracer(settings.enable_tracing)
        client = self.client
        if client is None:
            raise RuntimeError("Client not initialized")

        with tracer.trace("commit"):
            response_text = client.invoke(full_prompt, settings.llm_timeout_seconds)

        def retry_fn(retry_message: str) -> str:
            retry_prompt = f"{COMMIT_SYSTEM_PROMPT}\n\n{retry_message}\n\nChange summary: {message}"
            with tracer.trace("commit"):
                return client.invoke(retry_prompt, settings.llm_timeout_seconds)

        payload = parse_json_strict(response_text, schema_hint, retry_fn=retry_fn)
        result = CommitResult.model_validate(payload)
        if plan_id or task_id:
            return result.model_copy(update={"plan_id": plan_id, "task_id": task_id})
        return result
