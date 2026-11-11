"""P4-2 — Bộ kiểm duyệt câu trả lời độc lập.

Module này chạy SAU khi câu trả lời đã được sinh ra (thường là bởi LLM) và có quyền
CHẶN, tức là thay toàn bộ câu trả lời bằng một cảnh báo cố định.

Vì sao tách riêng thay vì nhét thêm luật vào prompt:
- Prompt chỉ là "lời dặn" cho LLM; model nhỏ như qwen2.5:3b vẫn có thể bỏ qua.
- Reviewer là luật thuần Python, không gọi Ollama, nên độc lập với model sinh câu trả lời,
  chạy ổn định (cùng đầu vào → cùng kết quả) và kiểm thử được bằng unit test.

Phạm vi luật: chỉ gồm nhóm thao tác LUÔN bị cấm với người dùng phổ thông (làm việc khi
còn điện, vô hiệu hóa thiết bị bảo vệ, can thiệp linh kiện năng lượng cao, gas lạnh,
tự đấu nối điện lưới, mở vỏ thiết bị). Nhóm này bị chặn kể cả khi câu trả lời có nhắc
"ngắt nguồn trước", vì ví dụ tụ điện vẫn giữ điện sau khi rút phích cắm.
Các thao tác bảo dưỡng thông thường trong sách hướng dẫn (rút phích rồi vệ sinh lưới
lọc, lau gioăng...) cố ý KHÔNG có trong luật để tránh chặn nhầm.
"""

import re
from dataclasses import dataclass

# Cảnh báo thay thế khi câu trả lời bị chặn. Nội dung nói về THAO TÁC nguy hiểm, khác với
# EMERGENCY_RESPONSE (dùng khi chính người dùng đang gặp tình huống nguy hiểm).
UNSAFE_ANSWER_RESPONSE = (
    "Mình không thể đưa ra hướng dẫn này vì nó có thể liên quan tới thao tác "
    "nguy hiểm với điện. Hãy rút phích cắm hoặc ngắt cầu dao, không tự tháo vỏ "
    "hay sửa bên trong thiết bị, và liên hệ trung tâm bảo hành hoặc thợ có "
    "chuyên môn để được kiểm tra an toàn."
)


@dataclass(frozen=True)
class ReviewDecision:
    """Kết quả kiểm duyệt: được phép trả về hay phải chặn, kèm lý do để ghi trace."""

    allowed: bool
    reason: str
    matched_rules: tuple[str, ...] = ()


# Tên luật -> danh sách regex. Tên luật được ghi vào trace để biết vì sao bị chặn.
# Các regex chạy trên văn bản đã casefold và gộp khoảng trắng.
# `(?:\S+\s+){0,2}?` cho phép chen tối đa 2 từ, ví dụ "tháo bỏ [luôn cái] cầu chì".
_UNSAFE_RULES: dict[str, tuple[re.Pattern[str], ...]] = {
    # Thao tác trên thiết bị/dây khi vẫn còn điện.
    "live_work": (
        re.compile(
            r"\b(?:chạm|sờ|cầm|đo|kiểm tra|thử|tháo|sửa|vệ sinh|lau)\b"
            r"[^.!?;\n]{0,40}?\b(?:khi|lúc|trong lúc|trong khi)\s+"
            r"(?:\S+\s+){0,2}?(?:vẫn|còn|đang)\s+"
            r"(?:cắm điện|cắm nguồn|cắm|có điện|có nguồn|cấp điện)"
        ),
        re.compile(
            r"\bkhông cần\s+(?:phải\s+)?(?:ngắt|rút|tắt)\s+"
            r"(?:điện|nguồn|phích|cầu dao|aptomat)"
        ),
        re.compile(r"\bđo\s+(?:điện áp|hiệu điện thế|dòng điện)\b"),
        re.compile(
            r"\b(?:chạm|sờ|cầm)\s+(?:thử\s+)?(?:tay\s+)?(?:vào\s+)?"
            r"(?:dây điện|dây nguồn|lõi dây|đầu dây|cực|chân phích|lỗ ổ cắm)"
        ),
    ),
    # Vô hiệu hóa hoặc thay thế sai thiết bị bảo vệ.
    "bypass_protection": (
        re.compile(
            r"\b(?:nối tắt|đấu tắt|câu tắt|bỏ qua|vô hiệu hóa|tháo bỏ|cắt bỏ|bỏ)\s+"
            r"(?:\S+\s+){0,2}?"
            r"(?:cầu chì|aptomat|áp tô mát|cb\b|cầu dao chống giật|elcb|rcd|rcbo|"
            r"rơ le nhiệt|rơle nhiệt|công tắc an toàn|tiếp địa|dây tiếp đất|"
            r"dây nối đất)"
        ),
        re.compile(r"\bthay\s+cầu chì\s+bằng\s+(?:dây|sợi|giấy bạc|kim loại)"),
    ),
    # Linh kiện có thể giữ điện áp/năng lượng cao kể cả khi đã rút nguồn.
    "high_energy_component": (
        re.compile(r"\bxả\s+(?:điện\s+)?(?:\S+\s+){0,1}?tụ\b"),
        re.compile(
            r"\b(?:tháo|mở|sửa|thay|hàn)\s+(?:\S+\s+){0,2}?"
            r"(?:magnetron|cao áp|bo mạch nguồn|bo nguồn|mạch nguồn|tụ điện|"
            r"tụ cao áp|máy nén|lốc máy|block máy)"
        ),
    ),
    # Gas lạnh cần thiết bị và chứng chỉ chuyên môn.
    "refrigerant_gas": (
        re.compile(
            r"\b(?:xả|nạp|bơm|thêm|châm)\s+(?:thêm\s+)?"
            r"(?:gas|ga lạnh|ga điều hòa|môi chất lạnh)"
        ),
    ),
    # Tự đấu nối điện lưới 220V.
    "mains_wiring": (
        re.compile(
            r"\b(?:đấu|nối)\s+(?:lại\s+)?(?:\S+\s+){0,1}?dây\s+(?:điện\s+)?"
            r"(?:220\s?v|nguồn|vào ổ|vào cầu dao|vào aptomat)"
        ),
        re.compile(r"\b(?:nối|đấu)\s+(?:thẳng|trực tiếp)\s+(?:vào\s+)?(?:nguồn|điện lưới|220\s?v)"),
        re.compile(r"\b(?:bóc|tuốt)\s+(?:vỏ\s+)?dây\s+(?:điện|nguồn)"),
    ),
    # Mở vỏ thiết bị để can thiệp bên trong (khác với mở nắp bộ lọc theo hướng dẫn).
    "open_enclosure": (
        re.compile(
            r"\b(?:tháo|mở|cạy)\s+(?:\S+\s+){0,2}?"
            r"(?:vỏ máy|vỏ thiết bị|vỏ ngoài|vỏ\b|nắp lưng|bo mạch)"
        ),
    ),
}

# Ranh giới câu: luật chỉ xét trong từng câu/dòng để phủ định ở câu trước không ảnh hưởng
# câu sau ("Đừng tháo vỏ. Hãy xả tụ..." → câu thứ hai vẫn bị chặn).
_SENTENCE_BOUNDARY = re.compile(r"[.!?;\n]+|\bnhưng\b")

# Từ cấm đoán trong câu TRẢ LỜI. Khác với _NEGATION_PATTERN ở domain/routing.py (dùng cho
# câu HỎI, chủ yếu mô tả "không có"/"chưa"): ở đây cần nhận các lời khuyên dạng mệnh lệnh
# như "tránh", "đừng", "không được". Không dùng chữ "không" đơn lẻ vì câu như
# "Nếu máy không chạy, hãy xả tụ" sẽ bị hiểu nhầm là phủ định.
_PROHIBITIVE_CUE = re.compile(
    r"\b(?:không được|không nên|không cần|không tự|không bao giờ|tuyệt đối không|"
    r"đừng|tránh|cấm|nghiêm cấm|chớ)\b"
)
# Từ khẳng định/mệnh lệnh làm "mất hiệu lực" lời cấm đứng trước nó trong cùng câu,
# ví dụ "Đừng hoảng, hãy xả tụ bằng tua vít" → vẫn là chỉ dẫn nguy hiểm.
_AFFIRMATIVE_CUE = re.compile(r"\b(?:hãy|sau đó|tiếp theo|rồi|bạn có thể)\b")


def review_answer(answer: str) -> ReviewDecision:
    """Kiểm tra câu trả lời có chứa chỉ dẫn thao tác điện nguy hiểm hay không."""
    # Giữ nguyên xuống dòng ở bước này vì mỗi dòng/gạch đầu dòng được xét như một câu.
    normalized = answer.casefold()
    matched: list[str] = []

    for sentence in _SENTENCE_BOUNDARY.split(normalized):
        sentence = " ".join(sentence.split())
        if not sentence:
            continue
        for rule_name, patterns in _UNSAFE_RULES.items():
            if rule_name in matched:
                continue
            if any(
                not _is_prohibited(sentence[: match.start()])
                for pattern in patterns
                for match in pattern.finditer(sentence)
            ):
                matched.append(rule_name)

    if matched:
        return ReviewDecision(
            allowed=False,
            reason="unsafe_instruction_detected",
            matched_rules=tuple(matched),
        )
    return ReviewDecision(allowed=True, reason="no_unsafe_instruction")


def _is_prohibited(prefix: str) -> bool:
    # Chỉ xem là lời cấm khi từ cấm đoán xuất hiện SAU từ khẳng định cuối cùng trong câu.
    prohibitive_end = max(
        (m.end() for m in _PROHIBITIVE_CUE.finditer(prefix)),
        default=-1,
    )
    affirmative_end = max(
        (m.end() for m in _AFFIRMATIVE_CUE.finditer(prefix)),
        default=-1,
    )
    return prohibitive_end > affirmative_end


class RuleBasedAnswerReviewer:
    """Adapter hiện thực port `AnswerReviewer` bằng bộ luật ở trên.

    `question` chưa được dùng: luật hiện tại chỉ xét câu trả lời. Tham số được giữ trong
    hợp đồng để sau này có thể cắm reviewer khác (ví dụ cần ngữ cảnh câu hỏi) mà không
    phải sửa ChatService.
    """

    def review(self, question: str, answer: str) -> ReviewDecision:
        return review_answer(answer)
