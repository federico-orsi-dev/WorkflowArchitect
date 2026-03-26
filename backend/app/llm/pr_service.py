from __future__ import annotations

import json

from app.core.settings import settings
from app.llm.client_factory import create_client
from app.llm.json_guard import parse_json_strict
from app.llm.prompts import PR_AGGREGATION_SYSTEM_PROMPT
from app.llm.tracing import get_tracer
from app.schemas.commit import CommitResult
from app.schemas.pr import PullRequestResult


class PullRequestService:
    def __init__(self) -> None:
        self.client = create_client(settings)

    def run(self, commits: list[CommitResult]) -> PullRequestResult:
        commit_lines: list[str] = []
        for index, commit in enumerate(commits, start=1):
            label_text = ", ".join(commit.labels) if commit.labels else "none"
            commit_lines.append(
                "\n".join(
                    [
                        f"{index}. {commit.commit_message}",
                        f"   PR title: {commit.pr_title}",
                        f"   PR body: {commit.pr_body_markdown}",
                        f"   Changelog: {commit.changelog_entry}",
                        f"   Labels: {label_text}",
                    ]
                )
            )

        if not self.client:
            commit_messages = [commit.commit_message for commit in commits]
            labels: list[str] = _merge_labels([], commits)
            body_lines = "\n".join([f"- {message}" for message in commit_messages]) or "- N/A"
            result = PullRequestResult(
                pr_title="Aggregate changes",
                pr_body_markdown=f"### Summary\n{body_lines}\n\n### How to test\n- N/A",
                changelog_entry="Changed: aggregate updates across multiple commits.",
                labels=labels,
            )
            return result

        schema_hint = json.dumps(
            {
                "pr_title": "...",
                "pr_body_markdown": "### Summary...### Impact...### How to test...",
                "changelog_entry": "Changed: ...",
                "labels": ["feature", "tests"],
            },
            indent=2,
        )

        commit_block = "\n".join(commit_lines)
        user_prompt = (
            "This pull request contains the following commits:\n"
            f"{commit_block}\n\n"
            "Produce a single PR title and PR body that:\n"
            "- Explains the global intent\n"
            "- Groups changes logically\n"
            "- Avoids repeating commit messages\n"
            "- Reads like a human-written PR\n\n"
            f"Schema:\n{schema_hint}"
        )
        full_prompt = f"{PR_AGGREGATION_SYSTEM_PROMPT}\n\n{user_prompt}"
        tracer = get_tracer(settings.enable_tracing)
        client = self.client
        if client is None:
            raise RuntimeError("Client not initialized")

        with tracer.trace("pr"):
            response_text = client.invoke(full_prompt, settings.llm_timeout_seconds)

        def retry_fn(retry_message: str) -> str:
            retry_prompt = f"{PR_AGGREGATION_SYSTEM_PROMPT}\n\n{retry_message}\n\n{user_prompt}"
            with tracer.trace("pr"):
                return client.invoke(retry_prompt, settings.llm_timeout_seconds)

        payload = parse_json_strict(response_text, schema_hint, retry_fn=retry_fn)
        result = PullRequestResult.model_validate(payload)
        merged_labels = _merge_labels(result.labels, commits)
        return result.model_copy(update={"labels": merged_labels})


def _merge_labels(existing: list[str], commits: list[CommitResult]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []

    def add(label: str) -> None:
        normalized = label.strip()
        if not normalized or normalized in seen:
            return
        seen.add(normalized)
        merged.append(normalized)

    for label in existing:
        add(label)
    for commit in commits:
        for label in commit.labels:
            add(label)

    return merged
