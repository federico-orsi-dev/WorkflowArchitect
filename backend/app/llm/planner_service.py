from __future__ import annotations

import json

from app.core.settings import settings
from app.llm.client_factory import create_client
from app.llm.json_guard import parse_json_strict
from app.llm.prompts import PLAN_SYSTEM_PROMPT
from app.llm.tracing import get_tracer
from app.schemas.plan import PlanResult


class PlannerService:
    def __init__(self) -> None:
        self.client = create_client(settings)

    def run(self, prompt: str) -> PlanResult:
        if not self.client:
            return PlanResult(
                tasks=[
                    {
                        "id": "t1",
                        "title": "Define scope",
                        "details": "Clarify the goal and success metrics.",
                        "estimate_minutes": 15,
                        "risk": "low",
                        "definition_of_done": ["Goal agreed", "Success metrics listed"],
                    }
                ],
                total_estimate_minutes=15,
                notes="Datapizza client not configured; using fallback plan.",
            )

        schema_hint = json.dumps(
            {
                "tasks": [
                    {
                        "id": "t1",
                        "title": "...",
                        "details": "...",
                        "estimate_minutes": 15,
                        "risk": "low|med|high",
                        "definition_of_done": ["...", "..."],
                    }
                ],
                "total_estimate_minutes": 110,
                "notes": "...",
            },
            indent=2,
        )

        user_prompt = f"User goal: {prompt}\n\nSchema:\n{schema_hint}"
        full_prompt = f"{PLAN_SYSTEM_PROMPT}\n\n{user_prompt}"
        tracer = get_tracer(settings.enable_tracing)

        with tracer.trace("plan"):
            response_text = self.client.invoke(full_prompt, settings.llm_timeout_seconds)

        def retry_fn(message: str) -> str:
            retry_prompt = f"{PLAN_SYSTEM_PROMPT}\n\n{message}\n\nUser goal: {prompt}"
            with tracer.trace("plan"):
                return self.client.invoke(retry_prompt, settings.llm_timeout_seconds)

        payload = parse_json_strict(response_text, schema_hint, retry_fn=retry_fn)
        # --- NORMALIZATION LLM OUTPUT (risk) ---
        for task in payload.get("tasks", []):
            risk = task.get("risk")
            if isinstance(risk, str):
                r = risk.lower().strip()
                if r in ("medium", "mid"):
                    task["risk"] = "med"
                elif r in ("low", "med", "high"):
                    task["risk"] = r
                else:
                    task["risk"] = "med"  # safe fallback

        return PlanResult.model_validate(payload)
