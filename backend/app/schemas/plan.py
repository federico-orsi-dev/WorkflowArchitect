from typing import Literal

from pydantic import BaseModel, Field, field_validator


class PlanRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=5,
        description="What should MicroPlanner produce?",
    )

    @field_validator("prompt")
    @classmethod
    def normalize_prompt(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 5:
            raise ValueError(
                "prompt must contain at least 5 non-whitespace characters."
            )
        return normalized


class PlanTask(BaseModel):
    id: str = Field(..., min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._:-]+$")
    title: str = Field(..., min_length=3, max_length=140)
    details: str = Field(..., min_length=5, max_length=1000)
    estimate_minutes: int = Field(..., ge=1, le=960)
    risk: Literal["low", "med", "high"]
    definition_of_done: list[str] = Field(..., min_length=1, max_length=10)

    @field_validator("title", "details")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("text fields must not be empty.")
        return normalized

    @field_validator("definition_of_done")
    @classmethod
    def normalize_definition_of_done(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value if item and item.strip()]
        if not normalized:
            raise ValueError("definition_of_done must contain at least one item.")
        return normalized


class PlanResult(BaseModel):
    tasks: list[PlanTask] = Field(..., min_length=1, max_length=20)
    total_estimate_minutes: int = Field(..., ge=1, le=10000)
    notes: str = Field(..., min_length=3, max_length=1000)

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("notes must not be empty.")
        return normalized


class PlanResponse(BaseModel):
    mode: Literal["PLAN"] = "PLAN"
    input: str
    result: PlanResult
