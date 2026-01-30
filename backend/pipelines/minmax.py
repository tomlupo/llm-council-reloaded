"""Minmax pipeline — decision support using minimax (maximize the minimum outcome)."""

import json
import re
from typing import Any, AsyncGenerator

from backend.pipelines.base import CouncilPipeline
from backend.prompts_modes import (
    MINMAX_ANALYSIS_PROMPT,
    MINMAX_ANALYSIS_SYSTEM,
    MINMAX_RECOMMENDATION_PROMPT,
    MINMAX_RECOMMENDATION_SYSTEM,
)
from backend.settings import get_settings


class MinmaxPipeline(CouncilPipeline):
    """Pipeline that evaluates options under worst-case assumptions and recommends the option that maximizes the minimum outcome."""

    async def execute(
        self, content: str, config: dict | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        cfg = config or {}
        options = cfg.get("options", [])
        criteria = cfg.get("criteria", get_settings().decide_defaults.criteria)

        if len(options) < 2:
            yield self._sse("error", message="At least 2 options are required for minmax mode")
            return

        yield self._sse("minmax_start", decision=content, options=options, criteria=criteria)

        # --- Stage 1: Individual minimax analyses ---
        yield self._sse("minmax_analysis_init", total=len(self.models))

        options_list = "\n".join(f"- {opt}" for opt in options)
        criteria_list = "\n".join(f"- {c}" for c in criteria)
        analysis_prompt = MINMAX_ANALYSIS_PROMPT.format(
            decision=content,
            options_list=options_list,
            criteria_list=criteria_list,
        )

        responses = await self._parallel_query(analysis_prompt, MINMAX_ANALYSIS_SYSTEM)

        analyses: list[dict] = []
        for resp in responses:
            if not resp.error:
                parsed = _parse_minmax_analysis(resp.response, options, criteria)
                parsed["model"] = resp.model_name
                analyses.append(parsed)
                yield self._sse(
                    "minmax_analysis_progress",
                    model=resp.model_name,
                    min_per_option=parsed.get("min_per_option", {}),
                    recommendation=parsed.get("recommendation", ""),
                )
            else:
                yield self._sse("minmax_analysis_progress", model=resp.model_name, error=resp.error)

        yield self._sse("minmax_analysis_complete", analyses=analyses)

        # --- Aggregate minimum scores per option ---
        aggregated_mins = _aggregate_min_scores(analyses, options)
        rec_counts = _count_recommendations(analyses)

        # --- Chairman recommendation ---
        yield self._sse("minmax_recommendation_start")

        chairman = self._select_chairman()
        analyses_text = ""
        for a in analyses:
            analyses_text += f"\n### {a.get('model', 'Unknown')}\n"
            analyses_text += f"Min per option: {a.get('min_per_option', {})}\n"
            analyses_text += f"Recommendation: {a.get('recommendation', 'N/A')}\n"
            analyses_text += f"Reasoning: {a.get('reasoning', 'N/A')}\n"

        rec_prompt = MINMAX_RECOMMENDATION_PROMPT.format(
            decision=content,
            options_text=", ".join(options),
            analyses_text=analyses_text,
        )
        rec_resp = await self._query_single(
            chairman, rec_prompt, MINMAX_RECOMMENDATION_SYSTEM
        )
        recommendation = rec_resp.response if not rec_resp.error else "Recommendation failed."

        yield self._sse(
            "minmax_recommendation_complete",
            chairman=chairman.name,
            content=recommendation,
            aggregated_mins=aggregated_mins,
            recommendation_counts=rec_counts,
        )

        # --- Final ---
        yield self._sse(
            "minmax_complete",
            content=recommendation,
            minmax={
                "analyses": analyses,
                "aggregated_mins": aggregated_mins,
                "recommendation_counts": rec_counts,
                "chairman_recommendation": {
                    "model": chairman.name,
                    "response": recommendation,
                },
            },
            metadata={
                "deliberation_mode": "minmax",
                "minmax_config": {"options": options, "criteria": criteria},
            },
        )


def _parse_minmax_analysis(
    response: str, options: list[str], criteria: list[str]
) -> dict:
    """Extract worst_case_scores, min_per_option, recommendation, reasoning from model response."""
    try:
        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        data = json.loads(json_match.group(1)) if json_match else json.loads(response)
        worst_case = data.get("worst_case_scores", {})
        min_per = data.get("min_per_option", {})
        # Compute min per option from worst_case_scores if not provided
        if not min_per and worst_case:
            for opt in options:
                scores = worst_case.get(opt, {})
                vals = [scores.get(c, 0) for c in criteria if scores.get(c) is not None]
                if vals:
                    min_per[opt] = min(vals)
        return {
            "worst_case_scores": worst_case,
            "min_per_option": min_per,
            "recommendation": data.get("recommendation", ""),
            "reasoning": data.get("reasoning", ""),
        }
    except (json.JSONDecodeError, KeyError):
        return {
            "worst_case_scores": {},
            "min_per_option": {},
            "recommendation": "",
            "reasoning": response[:500],
        }


def _aggregate_min_scores(analyses: list[dict], options: list[str]) -> dict[str, float]:
    """For each option, average the min scores reported across models."""
    totals: dict[str, list[float]] = {opt: [] for opt in options}
    for a in analyses:
        min_per = a.get("min_per_option", {})
        for opt in options:
            val = min_per.get(opt)
            if val is not None:
                totals[opt].append(float(val))
    return {opt: sum(v) / len(v) if v else 0 for opt, v in totals.items()}


def _count_recommendations(analyses: list[dict]) -> dict[str, int]:
    """Count how many models recommended each option."""
    counts: dict[str, int] = {}
    for a in analyses:
        rec = a.get("recommendation", "")
        if rec:
            counts[rec] = counts.get(rec, 0) + 1
    return counts
