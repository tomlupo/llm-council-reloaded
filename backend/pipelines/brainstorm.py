"""Brainstorm pipeline — collaborative ideation with cross-pollination rounds."""

import re
from typing import Any, AsyncGenerator

from backend.council import ModelResponse
from backend.pipelines.base import CouncilPipeline
from backend.prompts_modes import (
    BRAINSTORM_CROSS_POLLINATION_PROMPT,
    BRAINSTORM_CROSS_POLLINATION_SYSTEM,
    BRAINSTORM_ROUND1_PROMPT,
    BRAINSTORM_STYLES,
    BRAINSTORM_SYNTHESIS_PROMPT,
    BRAINSTORM_SYNTHESIS_SYSTEM,
)
from backend.settings import get_settings


class BrainstormPipeline(CouncilPipeline):
    async def execute(self, content: str, config: dict | None = None) -> AsyncGenerator[dict[str, Any], None]:
        cfg = config or {}
        defaults = get_settings().brainstorm_defaults
        style_name = cfg.get("style", defaults.style)
        rounds = cfg.get("rounds", defaults.rounds)
        style_config = BRAINSTORM_STYLES.get(style_name, BRAINSTORM_STYLES["balanced"])

        yield self._sse("brainstorm_start", topic=content, style=style_name, rounds=rounds)

        # --- Round 1: Independent idea generation ---
        yield self._sse("brainstorm_round_start", round=1, type="initial")
        yield self._sse("brainstorm_round_init", total=len(self.models))

        round1_prompt = BRAINSTORM_ROUND1_PROMPT.format(
            topic=content,
            idea_count=style_config["idea_count"],
            prompt_modifier=style_config["prompt_modifier"],
        )
        system = f"You are brainstorming. {style_config['prompt_modifier']}"
        round1_responses = await self._parallel_query(round1_prompt, system)

        all_ideas: dict[str, list[str]] = {}
        round1_data: list[dict] = []
        for resp in round1_responses:
            if not resp.error:
                parsed = _parse_ideas(resp.response)
                all_ideas[resp.model_name] = parsed
                entry = {"model": resp.model_name, "response": resp.response,
                         "parsed_ideas": parsed, "latency_ms": resp.latency_ms}
            else:
                entry = {"model": resp.model_name, "error": resp.error}
            round1_data.append(entry)
            yield self._sse("brainstorm_round_progress", **entry)

        yield self._sse("brainstorm_round_complete", round=1, responses=round1_data)

        # --- Cross-pollination rounds ---
        all_rounds: list[dict] = [{"round_num": 1, "type": "initial", "responses": round1_data}]

        for round_num in range(2, rounds + 1):
            yield self._sse("brainstorm_round_start", round=round_num, type="cross_pollination")
            yield self._sse("brainstorm_round_init", total=len(self.models))

            # Build anonymized ideas text from all previous ideas
            ideas_text = _format_ideas_for_prompt(all_ideas)
            cross_prompt = BRAINSTORM_CROSS_POLLINATION_PROMPT.format(
                topic=content,
                ideas_text=ideas_text,
                round_display=round_num,
            )
            cross_responses = await self._parallel_query(cross_prompt, BRAINSTORM_CROSS_POLLINATION_SYSTEM)

            round_data: list[dict] = []
            for resp in cross_responses:
                if not resp.error:
                    parsed = _parse_ideas(resp.response)
                    # Add new ideas to the pool
                    existing = all_ideas.get(resp.model_name, [])
                    all_ideas[resp.model_name] = existing + parsed
                    entry = {"model": resp.model_name, "response": resp.response,
                             "parsed_ideas": parsed, "latency_ms": resp.latency_ms}
                else:
                    entry = {"model": resp.model_name, "error": resp.error}
                round_data.append(entry)
                yield self._sse("brainstorm_round_progress", **entry)

            all_rounds.append({"round_num": round_num, "type": "cross_pollination", "responses": round_data})
            yield self._sse("brainstorm_round_complete", round=round_num, responses=round_data)

        # --- Chairman synthesis ---
        yield self._sse("brainstorm_synthesis_start")

        chairman = self._select_chairman()
        all_ideas_text = _format_all_ideas_for_synthesis(all_ideas, all_rounds)
        synthesis_prompt = BRAINSTORM_SYNTHESIS_PROMPT.format(
            topic=content, all_ideas_text=all_ideas_text,
        )
        synth_resp = await self._query_single(chairman, synthesis_prompt, BRAINSTORM_SYNTHESIS_SYSTEM)
        synthesis = synth_resp.response if not synth_resp.error else "Synthesis failed."

        yield self._sse("brainstorm_synthesis_complete", chairman=chairman.name, content=synthesis)

        # --- Final ---
        yield self._sse("brainstorm_complete", content=synthesis, brainstorm={
            "style": style_name,
            "rounds": all_rounds,
            "synthesis": {"model": chairman.name, "response": synthesis},
        }, metadata={
            "deliberation_mode": "brainstorm",
            "brainstorm_config": {"style": style_name, "rounds": rounds},
        })


def _parse_ideas(response: str) -> list[str]:
    ideas = []
    for line in response.split("\n"):
        line = line.strip()
        match = re.match(r'^[\d\-\*\u2022]+[\.\)]\s*(.+)', line)
        if match:
            idea = match.group(1).strip()
            if idea and len(idea) > 10:
                ideas.append(idea)
    return ideas


def _format_ideas_for_prompt(all_ideas: dict[str, list[str]]) -> str:
    parts = []
    for i, (_, ideas) in enumerate(all_ideas.items()):
        parts.append(f"\n### Participant {chr(65 + i)}")
        for j, idea in enumerate(ideas[:5], 1):
            parts.append(f"{j}. {idea}")
    return "\n".join(parts)


def _format_all_ideas_for_synthesis(all_ideas: dict[str, list[str]], all_rounds: list[dict]) -> str:
    parts = []
    for rnd in all_rounds:
        label = "Round 1 Ideas" if rnd["type"] == "initial" else f"Round {rnd['round_num']} Ideas"
        parts.append(f"## {label}\n")
        for entry in rnd["responses"]:
            if "parsed_ideas" in entry:
                parts.append(f"### {entry['model']}")
                for i, idea in enumerate(entry["parsed_ideas"], 1):
                    parts.append(f"{i}. {idea}")
                parts.append("")
    return "\n".join(parts)
