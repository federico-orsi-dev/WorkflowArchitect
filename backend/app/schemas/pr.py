from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

CONVENTIONAL_COMMIT_PATTERN = (
    r"^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)"
    r"(\([a-zA-Z0-9._-]+\))?!?: .+"
)


class CommitSummary(BaseModel):
    commit_message: str = Field(
        ...,
        min_length=8,
        max_length=200,
        pattern=CONVENTIONAL_COMMIT_PATTERN,
    )
    labels: list[str] = Field(..., min_length=1, max_length=10)

    @field_validator("commit_message")
    @classmethod
    def normalize_commit_message(cls, value: str) -> str:
        return value.strip()

    @field_validator("labels")
    @classmethod
    def normalize_labels(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for item in value:
            label = item.strip().lower()
            if not label or label in seen:
                continue
            seen.add(label)
            normalized.append(label)
        if not normalized:
            raise ValueError("labels must contain at least one unique value.")
        return normalized


class PullRequestRequest(BaseModel):
    commits: list[CommitSummary] = Field(..., min_length=1, max_length=50)


class PullRequestResult(BaseModel):
    pr_title: str = Field(..., min_length=5, max_length=160)
    pr_body_markdown: str = Field(..., min_length=20, max_length=12000)
    changelog_entry: str = Field(..., min_length=8, max_length=500)
    labels: list[str] = Field(..., min_length=1, max_length=20)

    @field_validator("pr_title", "pr_body_markdown", "changelog_entry")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("text fields must not be empty.")
        return normalized

    @field_validator("labels")
    @classmethod
    def normalize_labels(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for item in value:
            label = item.strip().lower()
            if not label or label in seen:
                continue
            seen.add(label)
            normalized.append(label)
        if not normalized:
            raise ValueError("labels must contain at least one unique value.")
        return normalized

    @model_validator(mode="after")
    def ensure_required_sections(self) -> "PullRequestResult":
        body_lower = self.pr_body_markdown.lower()
        required_sections = ["why", "what", "how to test"]
        if not all(section in body_lower for section in required_sections):
            raise ValueError("pr_body_markdown must include Why, What, and How to test sections.")
        return self


class PullRequestResponse(BaseModel):
    mode: Literal["PR"] = "PR"
    input: list[CommitSummary]
    result: PullRequestResult
