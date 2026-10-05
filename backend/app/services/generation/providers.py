"""Generation providers. Mock mode is explicit and never a silent fallback."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx

from app.core.config import get_settings
from app.core.errors import AppError


@dataclass(frozen=True)
class GenerationResult:
    text: str
    provider: str
    model_id: str
    is_mock: bool


class GenerationProvider(ABC):
    provider_name: str
    is_mock: bool

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> GenerationResult:
        raise NotImplementedError

    @abstractmethod
    def health(self) -> dict[str, str]:
        raise NotImplementedError


class MockGenerationProvider(GenerationProvider):
    provider_name = "mock"
    is_mock = True

    def generate(self, system_prompt: str, user_prompt: str) -> GenerationResult:
        evidence_ids = _ids_from_prompt(user_prompt)
        claim_ids = evidence_ids[:1]
        snippet = _first_evidence_snippet(user_prompt)
        history_text = "MOCK/TEST OUTPUT: Review this labeled mock claim against the cited passage."
        if snippet:
            history_text = f"MOCK/TEST OUTPUT: Cited passage begins: {snippet}"
        payload = {
            "key_history": (
                [
                    {
                        "text": history_text,
                        "source_ids": claim_ids,
                        "evidence_status": "citation_present" if claim_ids else "needs_review",
                    }
                ]
                if claim_ids
                else []
            ),
            "current_documented_findings": [],
            "medications": [],
            "allergies": [],
            "laboratory_findings": [],
            "unresolved_or_unavailable": [
                "MOCK/TEST OUTPUT: This is labeled mock generation, not a clinical result."
            ],
            "processing_limitations": [
                "Generation provider is MOCK/TEST OUTPUT and must not be used in real evaluation metrics."
            ],
            "disclaimer": (
                "Research prototype for clinical-document summarization only. "
                "Not for diagnosis, prescribing, treatment recommendations, or autonomous "
                "clinical decision-making. Verify all generated information against the original records."
            ),
        }
        if "No evidence retrieved" in user_prompt:
            payload["key_history"] = []
            payload["unresolved_or_unavailable"] = [
                "MOCK/TEST OUTPUT: No evidence was supplied, so no facts were stated."
            ]
        return GenerationResult(
            text=json.dumps(payload),
            provider=self.provider_name,
            model_id="mock-test-v1",
            is_mock=True,
        )

    def health(self) -> dict[str, str]:
        return {"status": "ok", "provider": "mock", "warning": "MOCK/TEST OUTPUT"}


class OpenAICompatibleProvider(GenerationProvider):
    provider_name = "openai_compatible"
    is_mock = False

    def generate(self, system_prompt: str, user_prompt: str) -> GenerationResult:
        settings = get_settings()
        url = settings.generation_base_url.rstrip("/") + "/chat/completions"
        try:
            response = httpx.post(
                url,
                json={
                    "model": settings.generation_model,
                    "temperature": 0,
                    "max_tokens": settings.generation_max_output_tokens,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
                timeout=settings.generation_timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            raise AppError(status_code=504, detail="The generation provider timed out.") from exc
        except httpx.HTTPError as exc:
            raise AppError(status_code=503, detail="The generation provider is unavailable.") from exc
        if response.status_code >= 400:
            raise AppError(status_code=503, detail="The generation provider returned an error.")
        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as exc:
            raise AppError(status_code=502, detail="The generation provider returned malformed output.") from exc
        if not content or not str(content).strip():
            raise AppError(status_code=502, detail="The generation provider returned empty output.")
        return GenerationResult(
            text=str(content),
            provider=self.provider_name,
            model_id=settings.generation_model,
            is_mock=False,
        )

    def health(self) -> dict[str, str]:
        settings = get_settings()
        url = settings.generation_base_url.rstrip("/") + "/models"
        try:
            response = httpx.get(url, timeout=5)
        except httpx.HTTPError:
            return {"status": "unavailable", "provider": "openai_compatible"}
        if response.status_code >= 400:
            return {"status": "unavailable", "provider": "openai_compatible"}
        return {"status": "ok", "provider": "openai_compatible", "model": settings.generation_model}


def get_generation_provider() -> GenerationProvider:
    settings = get_settings()
    if settings.generation_provider == "mock":
        return MockGenerationProvider()
    if settings.generation_provider == "openai_compatible":
        return OpenAICompatibleProvider()
    raise AppError(status_code=500, detail="Unknown generation provider.")


def _ids_from_prompt(user_prompt: str) -> list[str]:
    ids: list[str] = []
    for line in user_prompt.splitlines():
        if line.startswith("[ID="):
            ids.append(line.split("ID=", 1)[1].split(" ", 1)[0].rstrip("]"))
    return ids


def _first_evidence_snippet(user_prompt: str, limit: int = 80) -> str:
    lines = user_prompt.splitlines()
    capture = False
    for line in lines:
        if line.startswith("[ID="):
            capture = True
            continue
        if capture:
            text = line.strip()
            if not text:
                continue
            return text[:limit]
    return ""
