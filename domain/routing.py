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
    "và tránh chạm vào thiết bị, dây điện hoặc khu vực đang ướt. Nếu có khói "
    "hay cháy, hãy rời khỏi khu vực và gọi lực lượng cứu hộ tại địa phương. "
    "Không tự tháo sửa; hãy nhờ người có chuyên môn kiểm tra."
)

_DEVICE_TERMS = (
    "máy giặt",
    "tủ lạnh",
    "tủ đông",
    "điều hòa",
    "máy lạnh",
    "bình nóng lạnh",
    "bình nước nóng",
    "nồi cơm điện",
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
    "đang sửa khi chưa ngắt điện",
    "tự sửa khi chưa ngắt điện",
    "chưa ngắt nguồn",
    "chưa ngắt điện",
    "nước vào ổ điện",
    "nước vào ổ cắm",
    "nước vào thiết bị đang cắm điện",
    "nước vào thiết bị đang cắm",
    "nước tràn vào ổ điện",
    "nước tràn vào ổ cắm",
    "tia lửa",
    "bốc cháy",
    "cháy",
    "khói",
    "mùi khét",
    "nổ",
)

_WATER_ELECTRIC_PATTERN = re.compile(
    r"\bnước\b.{0,30}\b(?:ổ điện|ổ cắm|thiết bị)\b"
    r".{0,30}\b(?:đang cắm điện|cắm điện|có điện)\b"
)
_NEGATION_PATTERN = re.compile(
    r"(?:^|\s)(?:không|chưa|chẳng|không bị|không có|không thấy|không còn)"
    r"(?:\s+\S+){0,4}\s*$"
)
_CLAUSE_BOUNDARY_PATTERN = re.compile(r"[,.;!?]|\bnhưng\b|\bcòn\b")
_SAFETY_CLAUSE_PATTERN = re.compile(
    r"\b(?:nếu|trường hợp|ví dụ|chẳng hạn)\b"
)

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


def clarification_fields_for(message: str) -> list[str]:
    """Choose basic missing fields until conversation state is wired into the API."""
    normalized = " ".join(message.casefold().split())
    if any(device in normalized for device in _DEVICE_TERMS):
        return ["symptoms"]
    return ["device", "symptoms"]


def _has_emergency_signal(message: str) -> bool:
    # Luật an toàn chạy trước các nhánh LLM/RAG; chỉ xét tín hiệu trong mệnh đề hiện tại.
    if _WATER_ELECTRIC_PATTERN.search(message):
        return True

    for term in _EMERGENCY_TERMS:
        start = 0
        while (match_start := message.find(term, start)) >= 0:
            prefix = message[max(0, match_start - 60) : match_start]
            clause = _CLAUSE_BOUNDARY_PATTERN.split(prefix)[-1]
            if (
                not _NEGATION_PATTERN.search(clause.rstrip())
                and not _SAFETY_CLAUSE_PATTERN.search(clause)
            ):
                return True
            start = match_start + len(term)
    return False


def _is_ambiguous(message: str) -> bool:
    if len(message.split()) < 2:
        return True
    return any(phrase in message for phrase in _AMBIGUOUS_PHRASES)
