import re
from dataclasses import dataclass
from enum import StrEnum

from domain.conversation import ConversationState


class Route(StrEnum):
    EMERGENCY = "emergency"
    DIRECT_ANSWER = "direct_answer"
    ASK_CLARIFICATION = "ask_clarification"
    RETRIEVE_DOCUMENTS = "retrieve_documents"


@dataclass(frozen=True)
class RouteDecision:
    route: Route
    reason: str


EMERGENCY_RESPONSE = (
    "Có thể đang có nguy cơ mất an toàn về điện. Hãy ngừng sử dụng thiết bị "
    "và tránh chạm vào thiết bị hoặc dây điện. Nếu có khói hay cháy, hãy rời "
    "khỏi khu vực và gọi lực lượng cứu hộ tại địa phương. Không tự tháo sửa; "
    "hãy liên hệ thợ điện hoặc trung tâm bảo hành đủ chuyên môn."
)

CLARIFICATION_RESPONSE = (
    "Bạn cho mình biết thiết bị nào đang gặp vấn đề, hãng/model nếu có, "
    "và hiện tượng cụ thể được không?"
)

NO_DOCUMENTS_RESPONSE = (
    "Mình chưa tìm thấy tài liệu phù hợp để trả lời chắc chắn. Bạn cho mình "
    "biết hãng và model thiết bị để mình có thể tra cứu chính xác hơn nhé."
)

_EMERGENCY_TERMS = (
    "điện giật",
    "bị giật khi chạm",
    "tê khi chạm",
    "rò điện",
    "rò rỉ điện",
    "chập điện",
    "chập cháy",
    "tia lửa",
    "bốc cháy",
    "cháy",
    "khói",
    "mùi khét",
    "nổ",
)

_NEGATION_PATTERN = re.compile(r"\b(?:không|chưa|chẳng|không bị|không có)\b")
_CLAUSE_BOUNDARY_PATTERN = re.compile(r"[,.;!?]|\bnhưng\b|\bcòn\b")

_AMBIGUOUS_PHRASES = (
    "giúp tôi",
    "tư vấn giúp",
    "còn cái này",
    "vậy thì sao",
    "như vậy thì sao",
    "nó bị vậy",
    "cái đó thì sao",
    "bị sao",
)

_DOCUMENT_INTENTS = (
    "bảo hành",
    "hướng dẫn",
    "manual",
    "sách hướng dẫn",
    "model",
    "mã lỗi",
    "khắc phục",
    "sửa ",
    "không lên nguồn",
    "không hoạt động",
    "không lạnh",
    "không nóng",
    "rung",
    "tiếng kêu",
    "vệ sinh",
    "bảo dưỡng",
    "bảo trì",
    "lắp đặt",
    "cài đặt",
    "thông số",
    "bao lâu",
    "cách dùng",
    "sử dụng",
    "tiết kiệm điện",
    "nhiệt độ",
)

_DIRECT_INTENTS = (
    "là gì",
    "nghĩa là gì",
    "tại sao",
    "vì sao",
    "nguyên lý",
    "có nên",
    "khác nhau",
)


def choose_route(
    message: str,
    state: ConversationState | None = None,
) -> RouteDecision:
    """Choose a safe action using deterministic rules before any LLM call."""
    normalized = " ".join(message.casefold().split())

    if state is not None and state.risk_level == "high":
        return RouteDecision(Route.EMERGENCY, "conversation_has_high_risk")

    if _has_emergency_signal(normalized):
        return RouteDecision(Route.EMERGENCY, "emergency_signal_detected")

    if _is_ambiguous(normalized):
        return RouteDecision(Route.ASK_CLARIFICATION, "message_is_ambiguous")

    if any(intent in normalized for intent in _DOCUMENT_INTENTS):
        return RouteDecision(Route.RETRIEVE_DOCUMENTS, "document_intent_detected")

    if any(intent in normalized for intent in _DIRECT_INTENTS):
        return RouteDecision(Route.DIRECT_ANSWER, "general_question_detected")

    return RouteDecision(Route.ASK_CLARIFICATION, "no_rule_matched")


def _has_emergency_signal(message: str) -> bool:
    for term in _EMERGENCY_TERMS:
        start = 0
        while (match_start := message.find(term, start)) >= 0:
            prefix = message[max(0, match_start - 60) : match_start]
            clause = _CLAUSE_BOUNDARY_PATTERN.split(prefix)[-1]
            if not _NEGATION_PATTERN.search(clause):
                return True
            start = match_start + len(term)
    return False


def _is_ambiguous(message: str) -> bool:
    if len(message.split()) < 2:
        return True
    return any(phrase in message for phrase in _AMBIGUOUS_PHRASES)
