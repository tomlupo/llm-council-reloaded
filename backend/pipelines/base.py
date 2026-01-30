"""Abstract base class for council pipelines."""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator

from backend.council import (
    ModelResponse,
    anonymize_responses,
    get_enabled_models,
    parallel_query,
    query_model,
    select_chairman,
)
from backend.settings import ModelConfig


class CouncilPipeline(ABC):
    """Base class for all deliberation pipelines.

    Subclasses implement execute() as an async generator that yields
    SSE event dicts: {"event": "...", "data": {...}}.
    """

    def __init__(self, models: list[ModelConfig] | None = None):
        self.models = models or get_enabled_models()
        if len(self.models) < 2:
            raise ValueError("Council requires at least 2 enabled models")

    @abstractmethod
    async def execute(self, content: str, config: dict | None = None) -> AsyncGenerator[dict[str, Any], None]:
        """Yield SSE event dicts throughout pipeline execution."""
        ...  # pragma: no cover
        # Make this an async generator
        if False:  # type: ignore[unreachable]
            yield {}

    # --- Shared helpers ---

    async def _parallel_query(
        self,
        prompt: str,
        system_prompt: str | None = None,
        models: list[ModelConfig] | None = None,
    ) -> list[ModelResponse]:
        return await parallel_query(models or self.models, prompt, system_prompt)

    async def _query_single(
        self,
        model: ModelConfig,
        prompt: str,
        system_prompt: str | None = None,
    ) -> ModelResponse:
        return await query_model(model, prompt, system_prompt)

    def _anonymize(
        self, responses: list[ModelResponse], prefix: str = "Response"
    ) -> tuple[dict[str, str], list[tuple[str, str]]]:
        return anonymize_responses(responses, prefix)

    def _select_chairman(self) -> ModelConfig:
        return select_chairman(self.models)

    def _format_responses_text(self, anonymized: list[tuple[str, str]]) -> str:
        return "\n\n".join(f"### {aid}\n{text}" for aid, text in anonymized)

    @staticmethod
    def _sse(event: str, **data: Any) -> dict[str, Any]:
        return {"event": event, "data": data}
