"""All mode-specific prompt templates extracted for reuse."""


# =============================================================================
# ASK mode (existing 3-stage pipeline)
# =============================================================================

ASK_SYSTEM = "Answer the following question thoroughly and accurately."

PEER_REVIEW_PROMPT = """You are peer-reviewing responses to the following question:

## Original Question
{original_prompt}

## Responses to Evaluate
{responses_text}

## Your Task
For EACH response, provide:

1. **Scores** (1-{scale} for each criterion):
{criteria_text}

2. **Strengths**: What did this response do well? (2-3 bullet points)

3. **Weaknesses**: What did this response miss or could improve? (2-3 bullet points)

4. **Ranking**: Rank all responses from best to worst.

Format your evaluation as JSON:
```json
{{
  "evaluations": [
    {{
      "response_id": "Response A",
      "scores": {{"accuracy": 8, "completeness": 7}},
      "strengths": ["...", "..."],
      "weaknesses": ["...", "..."]
    }}
  ],
  "ranking": ["Response A", "Response B"]
}}
```
"""

PEER_REVIEW_SYSTEM = "You are evaluating responses from other AI models. Be objective and thorough."

SYNTHESIS_PROMPT = """You are the Chairman of an LLM council. Multiple AI models have responded to a question, and each has peer-reviewed the others.

## Original Question
{original_prompt}

## Individual Responses
{responses_text}

## Peer Review Summary
{review_summary}

## Your Synthesis Task

Create a comprehensive final answer that:

1. **Consensus Points**: What did ALL or MOST models agree on? These are high-confidence findings.

2. **Disagreements**: Where did models differ? Explain the different perspectives and provide your resolution.

3. **Unique Insights**: Were there valuable points that only ONE model raised? Include these if they're valid.

4. **Final Answer**: Synthesize everything into a clear, actionable response to the original question.

Be decisive. Where models disagree, make a judgment call and explain your reasoning.
"""

SYNTHESIS_SYSTEM = "You are the Chairman of an LLM council. Synthesize all perspectives into a comprehensive final answer."


# =============================================================================
# DEBATE mode
# =============================================================================

DEBATE_OPENING_PROMPT = """You are participating in a structured debate on the following topic:

## Topic
{topic}

## Your Task
Present your opening statement:
1. **State your position** clearly (pro, con, or nuanced view)
2. **Provide 3-4 key arguments** supporting your position
3. **Include evidence or examples** for each argument
4. **Anticipate counterarguments** briefly

Keep your response focused and persuasive. You do not know what positions other debaters will take.
"""

DEBATE_OPENING_SYSTEM = "You are participating in a structured debate. Present your position clearly with evidence."

DEBATE_REBUTTAL_PROMPT = """## Debate Topic
{topic}

## Previous Arguments (Anonymized)
{debate_history}

## Rebuttal Round {round_num}

Now respond to the other positions:
1. **Address the strongest counterarguments** to your position
2. **Point out weaknesses** in opposing arguments
3. **Strengthen your case** with additional evidence
4. **Find common ground** where possible

Be respectful but incisive. Focus on the arguments, not the debaters.
"""

DEBATE_REBUTTAL_SYSTEM = "You are in the rebuttal phase. Address counterarguments and strengthen your position."

DEBATE_VERDICT_PROMPT = """You are the Chairman of this debate. Review all arguments and provide your verdict.

## Topic
{topic}

{all_arguments}

## Your Verdict

Provide:
1. **Strongest Arguments Per Position**: What were the best points on each side?
2. **Areas of Agreement**: What did all debaters agree on?
3. **Key Disagreements**: Where did they fundamentally differ?
4. **Your Verdict**: Based on argument quality, which position is most defensible? Why?

Be balanced but decisive. It's okay to declare a winner if one position was clearly stronger.
"""

DEBATE_VERDICT_SYSTEM = "You are a fair and analytical debate judge."


# =============================================================================
# DECIDE mode
# =============================================================================

DECIDE_ANALYSIS_PROMPT = """You are evaluating options for a decision.

## Decision
{decision}

## Options to Evaluate
{options_list}

## Evaluation Criteria
{criteria_list}

## Your Task

1. **Score each option** (1-10) for each criterion

2. **List pros and cons** for each option (3-4 each)

3. **Provide your recommendation** with reasoning

Format your response as JSON:
```json
{{
  "scores": {{
    "Option1": {{"criterion1": 8, "criterion2": 7}},
    "Option2": {{"criterion1": 6, "criterion2": 9}}
  }},
  "pros_cons": {{
    "Option1": {{
      "pros": ["pro1", "pro2", "pro3"],
      "cons": ["con1", "con2", "con3"]
    }},
    "Option2": {{
      "pros": ["..."],
      "cons": ["..."]
    }}
  }},
  "recommendation": "Option1",
  "reasoning": "Your detailed reasoning here..."
}}
```

Be objective and thorough. Consider real-world implications.
"""

DECIDE_ANALYSIS_SYSTEM = "You are a technical analyst. Provide objective, evidence-based analysis."

DECIDE_RECOMMENDATION_PROMPT = """You are synthesizing decision analyses from multiple AI models.

## Decision
{decision}

## Options
{options_text}

## Individual Analyses
{analyses_text}

## Your Task

Provide the final recommendation:

1. **Aggregated Scores**: Average scores across all models per option
2. **Consensus Points**: What do all models agree on?
3. **Contested Points**: Where do models disagree? Resolve these.
4. **Final Recommendation**: Which option is best? With confidence level.
5. **When to Choose Differently**: Situations where other options make sense.

Be decisive but acknowledge trade-offs.
"""

DECIDE_RECOMMENDATION_SYSTEM = "You are a senior technical advisor making a final recommendation."


# =============================================================================
# MINMAX mode (minimax decision: maximize the minimum outcome)
# =============================================================================

MINMAX_ANALYSIS_PROMPT = """You are evaluating options using a minimax (worst-case) lens.

## Decision
{decision}

## Options to Evaluate
{options_list}

## Evaluation Criteria
{criteria_list}

## Your Task (Minimax)

For each option, consider the **worst-case scenario**: what is the minimum payoff if things go badly?
1. **Score each option** (1-10) for each criterion under a **pessimistic / worst-case** assumption
2. For each option, compute the **minimum** score across criteria (its worst-case outcome)
3. Identify which option **maximizes** this minimum (best of the worst)
4. Provide brief reasoning for your worst-case scores and recommendation

Format your response as JSON:
```json
{{
  "worst_case_scores": {{
    "Option1": {{"criterion1": 4, "criterion2": 3}},
    "Option2": {{"criterion1": 5, "criterion2": 4}}
  }},
  "min_per_option": {{
    "Option1": 3,
    "Option2": 4
  }},
  "recommendation": "Option2",
  "reasoning": "Under worst-case assumptions, Option2 has the highest minimum..."
}}
```

Be conservative: assume setbacks, delays, or adverse conditions when scoring.
"""

MINMAX_ANALYSIS_SYSTEM = "You are a risk-aware analyst. Evaluate options under worst-case assumptions."

MINMAX_RECOMMENDATION_PROMPT = """You are synthesizing minimax analyses from multiple AI models.

## Decision
{decision}

## Options
{options_text}

## Individual Minimax Analyses
{analyses_text}

## Your Task

Apply minimax at the council level:

1. **Aggregated minimum scores**: For each option, consider the minimum scores reported across models (or average of per-model minimums)
2. **Worst-case consensus**: Which option do models agree is safest under adverse conditions?
3. **Final recommendation**: Which option maximizes the minimum outcome? With confidence level.
4. **When to choose differently**: Situations where a riskier option might be acceptable.

Be decisive. The minimax choice is the option that is best when things go wrong.
"""

MINMAX_RECOMMENDATION_SYSTEM = "You are a senior advisor applying minimax (maximize the minimum outcome) to reach a final recommendation."


# =============================================================================
# BRAINSTORM mode
# =============================================================================

BRAINSTORM_STYLES = {
    "wild": {
        "description": "creative and unconventional",
        "prompt_modifier": "Be creative and unconventional. No idea is too wild. Think outside the box.",
        "idea_count": 7,
    },
    "practical": {
        "description": "feasible and implementable",
        "prompt_modifier": "Focus on practical, implementable ideas. Consider feasibility and resources.",
        "idea_count": 5,
    },
    "balanced": {
        "description": "mix of creative and practical",
        "prompt_modifier": "Balance creativity with practicality. Include both innovative and achievable ideas.",
        "idea_count": 5,
    },
}

BRAINSTORM_ROUND1_PROMPT = """## Brainstorming Topic
{topic}

## Your Task
Generate {idea_count}-10 ideas related to this topic.

Guidelines:
- {prompt_modifier}
- Don't filter yourself - include all ideas that come to mind
- Brief description for each (1-2 sentences)
- Number your ideas

Format:
1. **[Idea Title]**: Brief description
2. **[Idea Title]**: Brief description
...
"""

BRAINSTORM_CROSS_POLLINATION_PROMPT = """## Brainstorming Topic
{topic}

## Ideas from Other Participants
{ideas_text}

## Round {round_display}: Cross-Pollination

Now that you've seen others' ideas:
1. **Build on** 1-2 promising ideas from others
2. **Combine** ideas from different participants
3. **Generate** 2-3 new variations or improvements

Format each as:
- **[Idea Title]** (builds on Participant X's idea #Y): Description
- **[Combined Idea]** (combines X#1 + Y#2): Description
- **[New Variation]**: Description
"""

BRAINSTORM_CROSS_POLLINATION_SYSTEM = "Build on others' ideas. Combine, improve, and generate new variations."

BRAINSTORM_SYNTHESIS_PROMPT = """You are synthesizing a brainstorming session.

## Topic
{topic}

{all_ideas_text}

## Your Task

Create a synthesized output:

1. **Cluster Ideas**: Group related ideas into 3-5 themes

2. **Top Ideas by Category**:
   - High-Impact, Low-Effort (quick wins)
   - High-Impact, Medium-Effort (major initiatives)
   - Innovative/Long-term (future possibilities)

3. **Best Combinations**: Highlight the best hybrid ideas that emerged

4. **Recommended Next Steps**: What should be done first?

Be concise but comprehensive. Prioritize quality over quantity.
"""

BRAINSTORM_SYNTHESIS_SYSTEM = "You are synthesizing brainstorming results into actionable insights."
