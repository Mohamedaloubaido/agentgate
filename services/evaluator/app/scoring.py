import re
from dataclasses import dataclass


WORD_RE = re.compile(r"[\w'-]+", re.UNICODE)


def _tokens(text: str) -> set[str]:
    return {token.casefold() for token in WORD_RE.findall(text)}


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def token_recall(expected: str, actual: str) -> float:
    expected_tokens = _tokens(expected)
    if not expected_tokens:
        return 1.0
    actual_tokens = _tokens(actual)
    return len(expected_tokens & actual_tokens) / len(expected_tokens)


def required_term_score(required_terms: list[str], actual: str) -> float:
    if not required_terms:
        return 1.0
    haystack = actual.casefold()
    hits = sum(1 for term in required_terms if term.casefold() in haystack)
    return hits / len(required_terms)


@dataclass(frozen=True)
class HeuristicScore:
    correctness: float
    groundedness: float
    required_terms: float
    score: float
    passed: bool
    reason: str


def score_case(expected: str, actual: str, required_terms: list[str]) -> HeuristicScore:
    correctness = token_recall(expected, actual)
    terms = required_term_score(required_terms, actual)

    # In the local scorer, groundedness intentionally weights explicit required
    # facts more heavily than free-form token overlap.
    groundedness = clamp((0.35 * correctness) + (0.65 * terms))
    score = clamp((0.55 * correctness) + (0.30 * groundedness) + (0.15 * terms))
    passed = score >= 0.55 and terms >= 0.5

    if passed:
        reason = "Local checks found sufficient semantic overlap and required facts."
    elif terms < 0.5:
        reason = "One or more required facts are missing from the answer."
    else:
        reason = "The candidate answer diverges too far from the expected behavior."

    return HeuristicScore(
        correctness=round(correctness, 4),
        groundedness=round(groundedness, 4),
        required_terms=round(terms, 4),
        score=round(score, 4),
        passed=passed,
        reason=reason,
    )
