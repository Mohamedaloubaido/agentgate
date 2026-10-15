import json
import os

from pydantic import BaseModel, Field

from .scoring import HeuristicScore


class JudgeOutput(BaseModel):
    correctness: float = Field(ge=0, le=1)
    groundedness: float = Field(ge=0, le=1)
    required_terms: float = Field(ge=0, le=1)
    score: float = Field(ge=0, le=1)
    passed: bool
    reason: str


def llm_judge(input_text: str, expected: str, actual: str, required_terms: list[str]) -> HeuristicScore:
    """Evaluate an answer with the OpenAI Responses API.

    Live model calls are never required by CI. This provider is enabled only
    when the caller explicitly selects judge_mode=llm and OPENAI_API_KEY exists.
    Structured Outputs keeps judge responses type-safe.
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for judge_mode=llm")

    from openai import OpenAI

    client = OpenAI()
    model = os.getenv("AGENTGATE_JUDGE_MODEL", "gpt-5.5")

    instructions = """You are an evaluator for an AI agent reliability platform.
Score the candidate response against the expected behavior. Be strict, penalize
unsupported claims, and judge whether required facts are preserved."""

    payload = {
        "user_input": input_text,
        "expected_behavior": expected,
        "candidate_response": actual,
        "required_terms": required_terms,
    }

    response = client.responses.parse(
        model=model,
        instructions=instructions,
        input=json.dumps(payload, ensure_ascii=False),
        text_format=JudgeOutput,
        store=False,
    )

    data = response.output_parsed
    if data is None:
        raise RuntimeError("Judge returned no structured result")

    return HeuristicScore(
        correctness=data.correctness,
        groundedness=data.groundedness,
        required_terms=data.required_terms,
        score=data.score,
        passed=data.passed,
        reason=data.reason,
    )
