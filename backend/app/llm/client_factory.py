from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger
from app.core.settings import Settings

logger = get_logger()


@dataclass
class LlmClient:
    client: Any

    def invoke(self, prompt: str, timeout_seconds: int) -> str:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.client.invoke, prompt)
            try:
                response = future.result(timeout=timeout_seconds)
            except FutureTimeout as exc:
                raise TimeoutError("LLM request timed out") from exc
        return getattr(response, "text", str(response))


def create_client(settings: Settings) -> LlmClient | None:
    if not settings.openai_api_key:
        logger.info("datapizza_disabled", reason="missing_api_key")
        return None

    try:
        from datapizza.clients.openai import OpenAIClient  # type: ignore
    except ImportError:
        logger.warning("datapizza_missing", reason="openai_client_not_installed")
        return None

    client = OpenAIClient(api_key=settings.openai_api_key, model=settings.model_name)
    return LlmClient(client=client)
