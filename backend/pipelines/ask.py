"""Ask pipeline — existing 3-stage council (independent responses, peer review, synthesis)."""

import json
import re
from typing import Any, AsyncGenerator

from backend.council import ModelResponse
from backend.pipelines.base import CouncilPipeline
from backend.prompts_modes import (
    ASK_SYSTEM,
    PEER_REVIEW_PROMPT,
    PEER_REVIEW_SYSTEM,
    SYNTHESIS_PROMPT,
    SYNTHESIS_SYSTEM,
)
from backend.settings import get_settings


class AskPipeline(CouncilPipeline):
    async def execute(self, content: str, config: dict | None = None) -> AsyncGenerator[dict[str, Any], None]:
        cfg = config or {}
        execution_mode = cfg.get("execution_mode", "full")
        skip_peer_review = execution_mode == "chat_only"

        # --- Stage 1: Independent responses ---
        yield self._sse("stage1_start")
        yield self._sse("stage1_init", total=len(self.models), models=[m.name for m in self.models])

        responses = await self._parallel_query(content, ASK_SYSTEM)

        stage1_data = []
        for resp in responses:
            entry = {"model": resp.model_name, "response": resp.response,
                     "latency_ms": resp.latency_ms, "error": resp.error}
            stage1_data.append(entry)
            yield self._sse("stage1_progress", **entry)

        yield self._sse("stage1_complete", responses=stage1_data)

        if skip_peer_review:
            yield self._sse("ask_complete", content="", stage1=stage1_data)
            return

        # --- Stage 2: Peer review ---
        yield self._sse("stage2_start")

        settings = get_settings()
        scoring = settings.council.peer_review.scoring
        mapping, anonymized = self._anonymize(responses)

        if len(anonymized) < 2:
            stage2_data = []
            yield self._sse("stage2_complete", reviews=[], mapping=mapping)
        else:
            criteria = scoring.criteria
            scale = scoring.scale
            total_models = len(self.models)

            responses_text = self._format_responses_text(anonymized)
            criteria_text = "\n".join(f"- **{c.title()}** (1-{scale})" for c in criteria)
            prompt = PEER_REVIEW_PROMPT.format(
                original_prompt=content,
                responses_text=responses_text,
                scale=scale,
                criteria_text=criteria_text,
            )

            all_reviews: list[dict] = []
            for model in self.models:
                resp = await self._query_single(model, prompt, PEER_REVIEW_SYSTEM)
                if not resp.error:
                    parsed = _parse_peer_reviews(resp.response, model.name, criteria)
                    all_reviews.extend(parsed)
                yield self._sse(
                    "stage2_progress",
                    model=model.name,
                    reviewed_count=len(all_reviews),
                    total=total_models,
                )

            stage2_data = all_reviews
            yield self._sse("stage2_complete", reviews=stage2_data, mapping=mapping)

        # --- Stage 3: Synthesis ---
        yield self._sse("stage3_start")

        chairman = self._select_chairman()
        synthesis = await self._run_synthesis(content, responses, stage2_data, mapping, chairman.name)

        yield self._sse("stage3_complete", content=synthesis, chairman=chairman.name)
        yield self._sse("ask_complete", content=synthesis, stage1=stage1_data,
                        stage2=stage2_data, stage3=synthesis)

    async def _run_synthesis(
        self, original_prompt: str, responses: list[ModelResponse],
        reviews: list[dict], mapping: dict[str, str], chairman_name: str,
    ) -> str:
        responses_text = "\n\n".join(
            f"### {r.model_name}\n{r.response}" for r in responses if not r.error
        )
        review_summary = _summarize_reviews(reviews, mapping)

        prompt = SYNTHESIS_PROMPT.format(
            original_prompt=original_prompt,
            responses_text=responses_text,
            review_summary=review_summary,
        )

        chairman_model = next((m for m in self.models if m.name == chairman_name), self.models[0])
        resp = await self._query_single(chairman_model, prompt, SYNTHESIS_SYSTEM)
        return resp.response if not resp.error else f"Synthesis failed: {resp.error}"


def _parse_peer_reviews(review_text: str, reviewer_model: str, criteria: list[str]) -> list[dict]:
    try:
        json_match = re.search(r'```json\s*(.*?)\s*```', review_text, re.DOTALL)
        data = json.loads(json_match.group(1)) if json_match else json.loads(review_text)
        ranking = data.get("ranking", [])
        reviews = []
        for i, ev in enumerate(data.get("evaluations", [])):
            response_id = ev.get("response_id", f"Response {chr(65 + i)}")
            scores = ev.get("scores", {})
            for c in criteria:
                scores.setdefault(c, 5)
            rank = ranking.index(response_id) + 1 if response_id in ranking else i + 1
            reviews.append({
                "reviewer_model": reviewer_model,
                "reviewed_id": response_id,
                "scores": scores,
                "total_score": sum(scores.values()),
                "strengths": ev.get("strengths", []),
                "weaknesses": ev.get("weaknesses", []),
                "ranking": rank,
            })
        return reviews
    except (json.JSONDecodeError, KeyError, ValueError):
        return []


def _summarize_reviews(reviews: list[dict], mapping: dict[str, str]) -> str:
    if not reviews:
        return "No peer reviews available."

    scores_by: dict[str, list[int]] = {}
    for r in reviews:
        aid = r["reviewed_id"]
        scores_by.setdefault(aid, []).append(r["total_score"])

    lines = ["### Average Scores\n", "| Response | Model | Avg Score |", "|----------|-------|-----------|"]
    for aid, scores in sorted(scores_by.items()):
        avg = sum(scores) / len(scores) if scores else 0
        lines.append(f"| {aid} | {mapping.get(aid, '?')} | {avg:.1f} |")

    return "\n".join(lines)
