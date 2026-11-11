import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum

from domain.conversation import ConversationState


class Route(StrEnum):
    EMERGENCY = "emergency"
    REFUSE = "refuse"
    DIRECT_ANSWER = "direct_answer"
    ASK_CLARIFICATION = "ask_clarification"
    RETRIEVE_DOCUMENTS = "retrieve_documents"


@dataclass(frozen=True)
class RouteDecision:
    route: Route
    reason: str


EMERGENCY_RESPONSE = (
    "Có thể đang có nguy cơ mất an toàn về điện. Hãy ngừng sử dụng và tránh "
    "chạm vào thiết bị, dây điện hoặc khu vực đang ướt. Chỉ ngắt nguồn tại "
    "cầu dao ở nơi khô ráo, an toàn nếu có thể; không tiến vào vùng nguy hiểm. "
    "Nếu có người bị điện giật, bất tỉnh hoặc bị thương, gọi cấp cứu 115; nếu "
    "có khói hoặc cháy, rời khỏi khu vực và gọi cứu hỏa 114. Không tự tháo sửa; "
    "hãy nhờ người có chuyên môn kiểm tra."
)

REFUSAL_RESPONSE = (
    "Mình không thể hướng dẫn thao tác này vì có thể gây điện giật, cháy hoặc "
    "chấn thương. Không thực hiện hoặc tiếp tục thao tác; hãy giữ nguyên các "
    "thiết bị bảo vệ và nhờ kỹ thuật viên có chuyên môn xử lý."
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
    "giật điện",
    "bị giật khi chạm",
    "tê khi chạm",
    "tê tê",
    "tê tay",
    "giật nhẹ",
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
    "có khói",
    "bốc khói",
    "khói bốc",
    "khói xuất hiện",
    "khói trắng",
    "khói đen",
    "mùi khét",
    "nổ",
    "xẹt xẹt",
    "nhựa chảy",
    "tiếng nổ bụp",
)

_WATER_ELECTRIC_PATTERN = re.compile(
    r"\b(?:nuoc|bon tam)\b.{0,60}\b(?:o dien|o cam|day dien|phich cam)\b"
    r"|\bnuoc\b.{0,80}\b(?:dang cam dien|van dang cam dien|cam dien)\b"
    r"|\b(?:may say toc|thiet bi dang cam)\b.{0,60}\b(?:bon tam|nuoc)\b"
    r"|\b(?:o dien|o cam|day dien|phich cam)\b.{0,50}\b(?:nuoc|am|ngap|ro nuoc)\b"
    r"|\b(?:kep toc|vat kim loai)\b.{0,35}\b(?:lo o dien|o cam)\b"
)
_LIVE_WORK_PATTERN = re.compile(
    r"\b(?:dang|hien tai|luc nay)\b.{0,80}"
    r"(?:\b(?:thao|sua|thay|giu|cam|cham)\b.{0,60}"
    r"\b(?:day dien|day nguon|day ben trong|o cam|o dien)\b"
    r"|\b(?:chua ngat dien|chua ngat nguon)\b)"
)
_CONNECTED_INTERNAL_WORK_PATTERN = re.compile(
    r"\bday nguon\b.{0,30}\bvan cam\b.{0,80}"
    r"\b(?:cham|kiem tra|tho)\b.{0,40}\b(?:day ben trong|linh kien|ben trong)\b"
)
_FIRE_HAZARD_PATTERN = re.compile(r"\bnhua\b.{0,20}\bchay\b")
_NEGATION_PATTERN = re.compile(
    r"(?:^|\s)(?:khong|chua|chang|khong bi|khong co|khong thay|khong con)"
    r"(?:\s+\S+){0,4}\s*$"
)
_CLAUSE_BOUNDARY_PATTERN = re.compile(r"[,.;!?]|\bnhung\b|\bcon\b")
_SAFETY_CLAUSE_PATTERN = re.compile(
    r"\b(?:neu|truong hop|vi du|chang han)\b"
)

_REFUSAL_TERMS = (
    "nối tắt cầu chì",
    "thay cầu chì bằng dây đồng",
    "dây đồng thay cho cầu chì",
    "bỏ cb chống giật",
    "vô hiệu hóa cb",
    "bỏ dây tiếp địa",
    "tăng dòng định mức cb",
    "xả tụ điện",
    "xả tụ",
    "magnetron",
    "tự nạp gas",
    "nạp gas tại nhà",
    "thay điện trở",
    "đấu lại cuộn dây",
    "nối hai đầu dây",
    "giữ dây điện vừa bật cb",
)
_REFUSAL_PATTERNS = (
    re.compile(r"\bday tiep dia\b.{0,80}\bbo\b"),
    re.compile(r"\bcb\b.{0,60}\b(?:dong dinh muc lon hon|dinh muc lon hon)\b"),
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
    normalized = " ".join(_normalize_text(message).split())

    if state is not None and state.risk_level == "high":
        return RouteDecision(Route.EMERGENCY, "conversation_has_high_risk")

    if _has_emergency_signal(normalized):
        return RouteDecision(Route.EMERGENCY, "emergency_signal_detected")

    if any(
        _normalize_text(term) in normalized for term in _REFUSAL_TERMS
    ) or any(pattern.search(normalized) for pattern in _REFUSAL_PATTERNS):
        return RouteDecision(Route.REFUSE, "unsafe_instruction_requested")

    if _is_ambiguous(normalized):
        return RouteDecision(Route.ASK_CLARIFICATION, "message_is_ambiguous")

    if any(_normalize_text(intent) in normalized for intent in _DOCUMENT_INTENTS):
        return RouteDecision(Route.RETRIEVE_DOCUMENTS, "document_intent_detected")

    if any(_normalize_text(intent) in normalized for intent in _DIRECT_INTENTS):
        return RouteDecision(Route.DIRECT_ANSWER, "general_question_detected")

    return RouteDecision(Route.ASK_CLARIFICATION, "no_rule_matched")


def clarification_fields_for(message: str) -> list[str]:
    """Choose basic missing fields until conversation state is wired into the API."""
    normalized = " ".join(_normalize_text(message).split())
    if any(_normalize_text(device) in normalized for device in _DEVICE_TERMS):
        return ["symptoms"]
    return ["device", "symptoms"]


def _has_emergency_signal(message: str) -> bool:
    # Luật an toàn chạy trước các nhánh LLM/RAG; chỉ xét tín hiệu trong mệnh đề hiện tại.
    if (
        _has_unnegated_pattern(_WATER_ELECTRIC_PATTERN, message)
        or _has_unnegated_pattern(_LIVE_WORK_PATTERN, message)
        or _has_unnegated_pattern(_CONNECTED_INTERNAL_WORK_PATTERN, message)
        or _has_unnegated_pattern(_FIRE_HAZARD_PATTERN, message)
    ):
        return True

    for term in (_normalize_text(item) for item in _EMERGENCY_TERMS):
        term_pattern = re.compile(rf"\b{re.escape(term)}\b")
        for match in term_pattern.finditer(message):
            prefix = message[max(0, match.start() - 60) : match.start()]
            clause = _CLAUSE_BOUNDARY_PATTERN.split(prefix)[-1]
            if (
                not _NEGATION_PATTERN.search(clause.rstrip())
                and not _SAFETY_CLAUSE_PATTERN.search(clause)
            ):
                return True
    return False


def _has_unnegated_pattern(pattern: re.Pattern[str], message: str) -> bool:
    for match in pattern.finditer(message):
        prefix = message[max(0, match.start() - 60) : match.start()]
        clause = _CLAUSE_BOUNDARY_PATTERN.split(prefix)[-1]
        if (
            not _NEGATION_PATTERN.search(clause.rstrip())
            and not _SAFETY_CLAUSE_PATTERN.search(clause)
        ):
            return True
    return False


def _normalize_text(value: str) -> str:
    # Chuẩn hóa dấu để luật an toàn nhận được cả tiếng Việt gõ không dấu.
    decomposed = unicodedata.normalize("NFD", value.casefold())
    without_marks = "".join(
        character
        for character in decomposed
        if unicodedata.category(character) != "Mn"
    )
    return without_marks.replace("đ", "d")


def _is_ambiguous(message: str) -> bool:
    if len(message.split()) < 2:
        return True
    return any(_normalize_text(phrase) in message for phrase in _AMBIGUOUS_PHRASES)
