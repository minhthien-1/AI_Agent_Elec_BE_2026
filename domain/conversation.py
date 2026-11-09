from typing import Literal

from pydantic import BaseModel, ConfigDict


RiskLevel = Literal["unknown", "low", "medium", "high"]
ConversationStage = Literal[
    "clarifying",
    "safety_warning",
    "guidance",
    "completed",
]


class ConversationState(BaseModel):
    """Immutable summary of the facts and progress in one conversation."""

    model_config = ConfigDict(frozen=True)

    device: str | None = None
    symptoms: tuple[str, ...] = ()
    risk_level: RiskLevel = "unknown"
    asked_questions: tuple[str, ...] = ()
    stage: ConversationStage = "clarifying"


def transition_conversation(
    state: ConversationState,
    *,
    device: str | None = None,
    symptoms: tuple[str, ...] = (),
    risk_level: RiskLevel | None = None,
    asked_question: str | None = None,
    stage: ConversationStage | None = None,
) -> ConversationState:
    """Return a new state after applying facts and progress from one turn."""
    next_risk_level = risk_level or state.risk_level
    next_stage = (
        "safety_warning"
        if next_risk_level == "high"
        else stage or state.stage
    )

    return ConversationState(
        device=device.strip() if device and device.strip() else state.device,
        symptoms=_merge_unique(state.symptoms, symptoms),
        risk_level=next_risk_level,
        asked_questions=_merge_unique(
            state.asked_questions,
            (asked_question,) if asked_question else (),
        ),
        stage=next_stage,
    )


def _merge_unique(
    current: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    merged: list[str] = []
    seen: set[str] = set()

    for value in (*current, *additions):
        cleaned = value.strip()
        normalized = cleaned.casefold()
        if cleaned and normalized not in seen:
            merged.append(cleaned)
            seen.add(normalized)

    return tuple(merged)
