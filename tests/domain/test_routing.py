import pytest

from domain.conversation import ConversationState
from domain.routing import Route, choose_route


@pytest.mark.parametrize(
    "message",
    (
        "Máy giặt có mùi khét",
        "Có khói bốc ra từ tủ lạnh",
        "Tôi bị điện giật khi chạm vào máy nước nóng",
        "Tủ lạnh phát tia lửa",
        "Ổ điện bị rò điện",
        "Nước tràn vào ổ cắm",
        "Nước vào thiết bị vẫn đang cắm điện",
        "Tôi đang sửa máy giặt khi chưa ngắt điện",
        "Tôi chưa ngắt nguồn trước khi tháo thiết bị",
        "Thiết bị đang bốc cháy",
    ),
)
def test_routes_emergency_signals_before_other_intents(message: str):
    decision = choose_route(message)

    assert decision.route is Route.EMERGENCY


@pytest.mark.parametrize(
    ("message", "expected_route"),
    (
        ("Máy giặt không có mùi khét", Route.ASK_CLARIFICATION),
        ("Không thấy khói ở tủ lạnh", Route.ASK_CLARIFICATION),
        ("Không có nước vào ổ điện", Route.ASK_CLARIFICATION),
        (
            "Tôi sẽ không sửa thiết bị khi chưa ngắt nguồn",
            Route.RETRIEVE_DOCUMENTS,
        ),
        ("Nếu có mùi khét thì tôi nên làm gì?", Route.ASK_CLARIFICATION),
        (
            "Tôi đọc hướng dẫn về trường hợp bị điện giật",
            Route.RETRIEVE_DOCUMENTS,
        ),
    ),
)
def test_negated_hypothetical_or_quoted_signal_does_not_trigger_emergency(
    message: str,
    expected_route: Route,
):
    decision = choose_route(message)

    assert decision.route is expected_route


def test_conversation_high_risk_keeps_emergency_route():
    state = ConversationState(risk_level="high")

    decision = choose_route("Máy giặt là gì?", state)

    assert decision.route is Route.EMERGENCY


@pytest.mark.parametrize(
    "message",
    ("Giúp tôi", "Vậy thì sao?", "Máy giặt"),
)
def test_routes_ambiguous_messages_to_clarification(message: str):
    decision = choose_route(message)

    assert decision.route is Route.ASK_CLARIFICATION


@pytest.mark.parametrize(
    "message",
    (
        "Máy giặt không lên nguồn",
        "Tủ lạnh Panasonic bảo hành bao lâu?",
        "Hướng dẫn vệ sinh điều hòa",
    ),
)
def test_routes_manual_and_troubleshooting_requests_to_retrieval(message: str):
    decision = choose_route(message)

    assert decision.route is Route.RETRIEVE_DOCUMENTS


def test_routes_general_self_contained_questions_to_direct_answer():
    decision = choose_route("Điện là gì?")

    assert decision.route is Route.DIRECT_ANSWER
