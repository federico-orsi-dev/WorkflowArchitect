from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

CONVENTIONAL_COMMIT_PATTERN = (
    r"^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)"
    r"(\([a-zA-Z0-9._-]+\))?!?: .+"
)


class CommitRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=5,
        description="What should CommitSense refine?",
    )
    plan_id: str | None = Field(
        default=None,
        description="Associated plan id",
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9._:-]+$",
    )
    task_id: str | None = Field(
        default=None,
        description="Associated task id",
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9._:-]+$",
    )

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 5:
            raise ValueError("message must contain at least 5 non-whitespace characters.")
        return normalized

    @model_validator(mode="after")
    def validate_task_requires_plan(self) -> "CommitRequest":
        if self.task_id and not self.plan_id:
            raise ValueError("plan_id is required when task_id is provided.")
        return self


class CommitResult(BaseModel):
    commit_message: str = Field(
        ...,
        min_length=8,
        max_length=200,
        pattern=CONVENTIONAL_COMMIT_PATTERN,
    )
    pr_title: str | None = None
    pr_body_markdown: str | None = None
    changelog_entry: str | None = None
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


class CommitResponse(BaseModel):
    mode: Literal["COMMIT"] = "COMMIT"
    input: str
    result: CommitResult
