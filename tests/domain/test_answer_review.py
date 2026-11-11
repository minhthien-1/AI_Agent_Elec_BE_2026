import pytest

from domain.answer_review import (
    UNSAFE_ANSWER_RESPONSE,
    RuleBasedAnswerReviewer,
    review_answer,
)
from domain.routing import EMERGENCY_RESPONSE, NO_DOCUMENTS_RESPONSE
from infrastructure.tools.ask_clarification import AskClarificationTool


@pytest.mark.parametrize(
    ("answer", "rule"),
    (
        ("Bạn hãy chạm thử vào dây nguồn xem có ấm không.", "live_work"),
        ("Kiểm tra bo mạch khi máy vẫn đang cắm điện.", "live_work"),
        ("Bạn không cần ngắt điện, cứ lau trực tiếp.", "live_work"),
        ("Dùng đồng hồ đo điện áp tại ổ cắm.", "live_work"),
        ("Nếu cầu chì hay đứt, hãy nối tắt cầu chì để máy chạy.", "bypass_protection"),
        ("Có thể thay cầu chì bằng dây đồng.", "bypass_protection"),
        ("Tháo bỏ dây tiếp địa nếu bị rò.", "bypass_protection"),
        ("Rút phích cắm, sau đó xả tụ bằng tua vít.", "high_energy_component"),
        ("Bạn có thể tự thay tụ điện của quạt.", "high_energy_component"),
        ("Hãy nạp thêm gas cho điều hòa.", "refrigerant_gas"),
        ("Đấu dây nguồn trực tiếp vào cầu dao.", "mains_wiring"),
        ("Tháo vỏ máy ra để kiểm tra.", "open_enclosure"),
    ),
)
def test_blocks_unsafe_instructions(answer: str, rule: str):
    decision = review_answer(answer)

    assert decision.allowed is False
    assert decision.reason == "unsafe_instruction_detected"
    assert rule in decision.matched_rules


def test_power_off_mention_does_not_unlock_always_forbidden_action():
    # "Chặn luôn": nhắc ngắt nguồn không làm thao tác nguy hiểm trở nên an toàn.
    decision = review_answer("Ngắt nguồn trước, rồi tháo vỏ và xả tụ điện.")

    assert decision.allowed is False
    assert "high_energy_component" in decision.matched_rules
    assert "open_enclosure" in decision.matched_rules


@pytest.mark.parametrize(
    "answer",
    (
        "Không được chạm vào dây nguồn khi đang cắm điện.",
        "Tránh tự tháo vỏ máy.",
        "Đừng tự nạp gas, hãy gọi thợ điện lạnh.",
        "Tuyệt đối không nối tắt cầu chì.",
        "Bạn không nên tự xả tụ.",
        "Rút phích cắm rồi vệ sinh lưới lọc xơ vải.",
        "Mở nắp bộ lọc bơm xả và lau sạch.",
        "Kiểm tra dây nguồn có bị đứt hoặc dập không.",
        "Đặt nhiệt độ ngăn mát khoảng 3–5°C.",
    ),
)
def test_allows_warnings_and_routine_maintenance(answer: str):
    decision = review_answer(answer)

    assert decision.allowed is True, decision.matched_rules


def test_negation_in_previous_sentence_does_not_cover_next_sentence():
    decision = review_answer("Đừng tháo vỏ máy. Hãy xả tụ bằng tua vít.")

    assert decision.allowed is False
    assert decision.matched_rules == ("high_energy_component",)


def test_affirmative_cue_after_negation_still_blocks():
    decision = review_answer("Đừng lo, hãy xả tụ bằng tua vít.")

    assert decision.allowed is False


def test_checks_each_bullet_line():
    answer = "Các bước:\n- Rút phích cắm\n- Tháo vỏ máy\n- Kiểm tra dây"

    decision = review_answer(answer)

    assert decision.matched_rules == ("open_enclosure",)


@pytest.mark.parametrize(
    "template",
    (
        EMERGENCY_RESPONSE,
        NO_DOCUMENTS_RESPONSE,
        UNSAFE_ANSWER_RESPONSE,
        *AskClarificationTool._QUESTIONS.values(),
    ),
)
def test_fixed_templates_pass_reviewer(template: str):
    # Lưới an toàn: nếu sửa luật làm chặn nhầm các câu cố định thì test này báo đỏ.
    assert review_answer(template).allowed is True


def test_rule_based_reviewer_implements_port():
    reviewer = RuleBasedAnswerReviewer()

    assert reviewer.review("câu hỏi", "Tháo vỏ máy.").allowed is False
    assert reviewer.review("câu hỏi", "Vệ sinh lưới lọc.").allowed is True
