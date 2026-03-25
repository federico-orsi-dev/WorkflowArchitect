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

    def run(self, message: str) -> CommitResult:
        if not self.client:
            return CommitResult(
                commit_message="chore: add placeholder message",
                labels=["chore"],
            )

        schema_hint = json.dumps(
            {
                "commit_message": "feat(scope): ...",
                "labels": ["refactor", "tests"],
            },
            indent=2,
        )

        user_prompt = f"Change summary: {message}\n\nSchema:\n{schema_hint}"
        full_prompt = f"{COMMIT_SYSTEM_PROMPT}\n\n{user_prompt}"
        tracer = get_tracer(settings.enable_tracing)

        with tracer.trace("commit"):
            response_text = self.client.invoke(full_prompt, settings.llm_timeout_seconds)

        def retry_fn(retry_message: str) -> str:
            retry_prompt = f"{COMMIT_SYSTEM_PROMPT}\n\n{retry_message}\n\nChange summary: {message}"
            with tracer.trace("commit"):
                return self.client.invoke(retry_prompt, settings.llm_timeout_seconds)

        payload = parse_json_strict(response_text, schema_hint, retry_fn=retry_fn)
        return CommitResult.model_validate(payload)
