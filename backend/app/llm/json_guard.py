from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


class JsonParseError(ValueError):
    pass


def ensure_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _extract_first_json_block(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def _load_json(text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def parse_json_strict(
    text: str,
    schema_hint: str,
    retry_fn: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    direct = _load_json(text)
    if direct is not None:
        return direct

    extracted = _extract_first_json_block(text)
    if extracted:
        extracted_json = _load_json(extracted)
        if extracted_json is not None:
            return extracted_json

    if retry_fn is not None:
        retry_prompt = "Return ONLY valid JSON matching this schema, no prose."
        retry_text = retry_fn(f"{retry_prompt}\n\nSchema:\n{schema_hint}\n\nOutput:\n{text}")
        retry_loaded = _load_json(retry_text)
        if retry_loaded is not None:
            return retry_loaded
        extracted_retry = _extract_first_json_block(retry_text or "")
        if extracted_retry:
            extracted_json = _load_json(extracted_retry)
            if extracted_json is not None:
                return extracted_json

    raise JsonParseError("Model did not return valid JSON.")
