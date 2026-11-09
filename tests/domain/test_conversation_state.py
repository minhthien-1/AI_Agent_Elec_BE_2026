import pytest
from pydantic import ValidationError

from domain.conversation import ConversationState, transition_conversation


def test_state_defaults_to_an_unknown_conversation_being_clarified():
    state = ConversationState()

    assert state.device is None
    assert state.symptoms == ()
    assert state.risk_level == "unknown"
    assert state.asked_questions == ()
    assert state.stage == "clarifying"


def test_transition_returns_a_new_state_and_preserves_known_facts():
    initial = ConversationState(
        device="Máy giặt",
        symptoms=("Không lên nguồn",),
        asked_questions=("Có đèn báo không?",),
    )

    updated = transition_conversation(
        initial,
        symptoms=("Có mùi khét", " không lên nguồn "),
        asked_question="Có mùi khét hoặc dấu hiệu cháy không?",
        risk_level="high",
        stage="guidance",
    )

    assert updated is not initial
    assert updated.device == "Máy giặt"
    assert updated.symptoms == ("Không lên nguồn", "Có mùi khét")
    assert updated.asked_questions == (
        "Có đèn báo không?",
        "Có mùi khét hoặc dấu hiệu cháy không?",
    )
    assert updated.risk_level == "high"
    assert updated.stage == "safety_warning"
    assert initial.symptoms == ("Không lên nguồn",)
    assert initial.risk_level == "unknown"


def test_transition_can_advance_to_guidance_when_risk_is_not_high():
    initial = ConversationState(
        device="Tủ lạnh",
        symptoms=("Không lạnh",),
        risk_level="low",
    )

    updated = transition_conversation(initial, stage="guidance")

    assert updated.stage == "guidance"
    assert updated.risk_level == "low"


def test_state_is_immutable_and_rejects_unknown_values():
    state = ConversationState()

    with pytest.raises(ValidationError):
        state.stage = "unknown_stage"

    with pytest.raises(ValidationError):
        ConversationState(risk_level="extreme")
