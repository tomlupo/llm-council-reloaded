"""Debate pipeline — multi-round structured debate with chairman verdict."""

from typing import Any, AsyncGenerator

from backend.council import ModelResponse
from backend.pipelines.base import CouncilPipeline
from backend.prompts_modes import (
    DEBATE_OPENING_PROMPT,
    DEBATE_OPENING_SYSTEM,
    DEBATE_REBUTTAL_PROMPT,
    DEBATE_REBUTTAL_SYSTEM,
    DEBATE_VERDICT_PROMPT,
    DEBATE_VERDICT_SYSTEM,
    PEER_REVIEW_PROMPT,
    PEER_REVIEW_SYSTEM,
)
from backend.settings import get_settings


class DebatePipeline(CouncilPipeline):
    async def execute(self, content: str, config: dict | None = None) -> AsyncGenerator[dict[str, Any], None]:
        cfg = config or {}
        rounds = cfg.get("rounds", get_settings().debate_defaults.rounds)
        positions = cfg.get("positions")

        yield self._sse("debate_start", topic=content, rounds=rounds)

        # --- Opening statements ---
        yield self._sse("debate_opening_init", total=len(self.models))

        opening_prompt = DEBATE_OPENING_PROMPT.format(topic=content)
        opening_responses = await self._parallel_query(opening_prompt, DEBATE_OPENING_SYSTEM)

        opening_data = []
        for resp in opening_responses:
            entry = {"model": resp.model_name, "response": resp.response,
                     "latency_ms": resp.latency_ms, "error": resp.error}
            opening_data.append(entry)
            yield self._sse("debate_opening_progress", **entry)

        yield self._sse("debate_opening_complete", responses=opening_data)

        # Build debate history (anonymized)
        debate_history = _format_debate_history(opening_responses, "Debater")

        # --- Rebuttal rounds ---
        all_rebuttals: list[list[dict]] = []
        for round_num in range(1, rounds):
            yield self._sse("debate_rebuttal_start", round=round_num)
            yield self._sse("debate_rebuttal_init", total=len(self.models))

            rebuttal_prompt = DEBATE_REBUTTAL_PROMPT.format(
                topic=content,
                debate_history=debate_history,
                round_num=round_num,
            )
            round_responses = await self._parallel_query(rebuttal_prompt, DEBATE_REBUTTAL_SYSTEM)

            round_data = []
            for resp in round_responses:
                entry = {"model": resp.model_name, "response": resp.response,
                         "latency_ms": resp.latency_ms, "error": resp.error}
                round_data.append(entry)
                yield self._sse("debate_rebuttal_progress", **entry)

            all_rebuttals.append(round_data)
            yield self._sse("debate_rebuttal_complete", round=round_num, responses=round_data)

            # Accumulate history for next round
            debate_history += "\n\n" + _format_debate_history(round_responses, "Debater")

        # --- Optional peer evaluation ---
        yield self._sse("debate_evaluation_start")

        settings = get_settings()
        scoring = settings.council.peer_review.scoring
        mapping, anonymized = self._anonymize(opening_responses, prefix="Debater")
        responses_text = self._format_responses_text(anonymized)
        criteria_text = "\n".join(f"- **{c.title()}** (1-{scoring.scale})" for c in scoring.criteria)

        eval_prompt = PEER_REVIEW_PROMPT.format(
            original_prompt=content,
            responses_text=responses_text,
            scale=scoring.scale,
            criteria_text=criteria_text,
        )

        eval_data: list[dict] = []
        for model in self.models:
            resp = await self._query_single(model, eval_prompt, PEER_REVIEW_SYSTEM)
            if not resp.error:
                eval_data.append({"model": resp.model_name, "evaluation": resp.response})
                yield self._sse("debate_evaluation_progress", model=resp.model_name)

        yield self._sse("debate_evaluation_complete", evaluations=eval_data, mapping=mapping)

        # --- Chairman verdict ---
        yield self._sse("debate_verdict_start")

        chairman = self._select_chairman()
        all_arguments = _build_all_arguments(opening_responses, all_rebuttals)
        verdict_prompt = DEBATE_VERDICT_PROMPT.format(
            topic=content, all_arguments=all_arguments,
        )
        verdict_resp = await self._query_single(chairman, verdict_prompt, DEBATE_VERDICT_SYSTEM)
        verdict = verdict_resp.response if not verdict_resp.error else "Verdict generation failed."

        yield self._sse("debate_verdict_complete", chairman=chairman.name, content=verdict)

        # --- Final ---
        yield self._sse("debate_complete", content=verdict, debate={
            "opening": opening_data,
            "rebuttals": all_rebuttals,
            "evaluation": eval_data,
            "verdict": {"model": chairman.name, "response": verdict},
        }, metadata={
            "deliberation_mode": "debate",
            "debate_config": {"rounds": rounds, "topic": content},
        })


def _format_debate_history(responses: list[ModelResponse], prefix: str) -> str:
    lines = []
    for i, resp in enumerate(responses):
        if not resp.error:
            lines.append(f"### {prefix} {chr(65 + i)}")
            lines.append(resp.response)
            lines.append("")
    return "\n".join(lines)


def _build_all_arguments(opening: list[ModelResponse], rebuttals: list[list[dict]]) -> str:
    parts = ["## Opening Statements\n"]
    for resp in opening:
        if not resp.error:
            parts.append(f"\n### {resp.model_name}\n{resp.response}\n")

    for i, round_data in enumerate(rebuttals):
        parts.append(f"\n## Rebuttal Round {i + 1}\n")
        for entry in round_data:
            if not entry.get("error"):
                parts.append(f"\n### {entry['model']}\n{entry['response']}\n")

    return "".join(parts)
