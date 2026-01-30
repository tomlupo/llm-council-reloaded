"""Decide pipeline — structured decision support with JSON scoring matrices."""

import json
import re
from typing import Any, AsyncGenerator

from backend.pipelines.base import CouncilPipeline
from backend.prompts_modes import (
    DECIDE_ANALYSIS_PROMPT,
    DECIDE_ANALYSIS_SYSTEM,
    DECIDE_RECOMMENDATION_PROMPT,
    DECIDE_RECOMMENDATION_SYSTEM,
    PEER_REVIEW_PROMPT,
    PEER_REVIEW_SYSTEM,
)
from backend.settings import get_settings

DEFAULT_CRITERIA = ["feasibility", "cost", "complexity", "maintainability"]


class DecidePipeline(CouncilPipeline):
    async def execute(self, content: str, config: dict | None = None) -> AsyncGenerator[dict[str, Any], None]:
        cfg = config or {}
        options = cfg.get("options", [])
        criteria = cfg.get("criteria", get_settings().decide_defaults.criteria)

        if len(options) < 2:
            yield self._sse("error", message="At least 2 options are required for decide mode")
            return

        yield self._sse("decide_start", decision=content, options=options, criteria=criteria)

        # --- Stage 1: Individual structured analyses ---
        yield self._sse("decide_analysis_init", total=len(self.models))

        options_list = "\n".join(f"- {opt}" for opt in options)
        criteria_list = "\n".join(f"- {c}" for c in criteria)
        analysis_prompt = DECIDE_ANALYSIS_PROMPT.format(
            decision=content, options_list=options_list, criteria_list=criteria_list,
        )

        responses = await self._parallel_query(analysis_prompt, DECIDE_ANALYSIS_SYSTEM)

        analyses: list[dict] = []
        for resp in responses:
            if not resp.error:
                parsed = _parse_analysis(resp.response, options, criteria)
                parsed["model"] = resp.model_name
                analyses.append(parsed)
                yield self._sse("decide_analysis_progress",
                                model=resp.model_name,
                                scores=parsed.get("scores", {}),
                                recommendation=parsed.get("recommendation", ""))
            else:
                yield self._sse("decide_analysis_progress",
                                model=resp.model_name, error=resp.error)

        yield self._sse("decide_analysis_complete", analyses=analyses)

        # --- Optional peer evaluation ---
        yield self._sse("decide_evaluation_start")

        settings = get_settings()
        scoring = settings.council.peer_review.scoring
        mapping, anonymized = self._anonymize(responses)
        responses_text = self._format_responses_text(anonymized)
        criteria_text = "\n".join(f"- **{c.title()}** (1-{scoring.scale})" for c in scoring.criteria)

        eval_prompt = PEER_REVIEW_PROMPT.format(
            original_prompt=f"Decision: {content}\nOptions: {', '.join(options)}",
            responses_text=responses_text,
            scale=scoring.scale,
            criteria_text=criteria_text,
        )

        eval_data: list[dict] = []
        for model in self.models:
            resp = await self._query_single(model, eval_prompt, PEER_REVIEW_SYSTEM)
            if not resp.error:
                eval_data.append({"model": resp.model_name, "evaluation": resp.response})
                yield self._sse("decide_evaluation_progress", model=resp.model_name)

        yield self._sse("decide_evaluation_complete", evaluations=eval_data)

        # --- Score aggregation ---
        aggregated = _aggregate_scores(analyses, options, criteria)
        rec_counts = _count_recommendations(analyses)

        # --- Chairman recommendation ---
        yield self._sse("decide_recommendation_start")

        chairman = self._select_chairman()
        analyses_text = ""
        for a in analyses:
            analyses_text += f"\n### {a.get('model', 'Unknown')}\n"
            analyses_text += f"Recommendation: {a.get('recommendation', 'N/A')}\n"
            analyses_text += f"Reasoning: {a.get('reasoning', 'N/A')}\n"

        rec_prompt = DECIDE_RECOMMENDATION_PROMPT.format(
            decision=content,
            options_text=", ".join(options),
            analyses_text=analyses_text,
        )
        rec_resp = await self._query_single(chairman, rec_prompt, DECIDE_RECOMMENDATION_SYSTEM)
        recommendation = rec_resp.response if not rec_resp.error else "Recommendation failed."

        yield self._sse("decide_recommendation_complete",
                        chairman=chairman.name, content=recommendation,
                        aggregated_scores=aggregated,
                        recommendation_counts=rec_counts)

        # --- Final ---
        yield self._sse("decide_complete", content=recommendation, decision={
            "analyses": analyses,
            "aggregated_scores": aggregated,
            "recommendation_counts": rec_counts,
            "chairman_recommendation": {"model": chairman.name, "response": recommendation},
        }, metadata={
            "deliberation_mode": "decide",
            "decide_config": {"options": options, "criteria": criteria},
        })


def _parse_analysis(response: str, options: list[str], criteria: list[str]) -> dict:
    try:
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        data = json.loads(json_match.group(1)) if json_match else json.loads(response)
        return {
            "scores": data.get("scores", {}),
            "pros_cons": data.get("pros_cons", {}),
            "recommendation": data.get("recommendation", ""),
            "reasoning": data.get("reasoning", ""),
        }
    except (json.JSONDecodeError, KeyError):
        return {
            "scores": {},
            "pros_cons": {},
            "recommendation": "",
            "reasoning": response[:500],
        }


def _aggregate_scores(analyses: list[dict], options: list[str], criteria: list[str]) -> dict[str, float]:
    totals: dict[str, list[float]] = {opt: [] for opt in options}
    for a in analyses:
        scores = a.get("scores", {})
        for opt in options:
            opt_scores = scores.get(opt, {})
            total = sum(opt_scores.get(c, 0) for c in criteria)
            if total > 0:
                totals[opt].append(total)
    return {opt: sum(v) / len(v) if v else 0 for opt, v in totals.items()}


def _count_recommendations(analyses: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for a in analyses:
        rec = a.get("recommendation", "")
        if rec:
            counts[rec] = counts.get(rec, 0) + 1
    return counts
