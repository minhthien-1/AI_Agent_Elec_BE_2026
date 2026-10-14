import math
import re
import unicodedata
from collections import defaultdict
from typing import DefaultDict, Dict, List, Set, Tuple

from document_processing.models import ExtractedDocument, TextBlock


_CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_WHITESPACE = re.compile(r"\s+")


def _normalize_line(line: str) -> str:
    return _WHITESPACE.sub(" ", line).strip().casefold()


def _is_margin_block(block: TextBlock, page_height: float) -> bool:
    if block.bbox is None or page_height <= 0:
        return False
    top, bottom = block.bbox[1], block.bbox[3]
    return top <= page_height * 0.12 or bottom >= page_height * 0.88


def _repeated_margin_lines(
    document: ExtractedDocument,
) -> Dict[int, Set[str]]:
    page_occurrences: DefaultDict[str, Set[int]] = defaultdict(set)

    if document.file_type != "pdf" or document.page_count < 2:
        return {}

    for page in document.pages:
        for block in page.blocks:
            if not _is_margin_block(block, page.height):
                continue
            for line in block.text.splitlines():
                normalized = _normalize_line(line)
                if normalized:
                    page_occurrences[normalized].add(page.page_number)

    threshold = max(2, math.ceil(document.page_count * 0.5))
    repeated = {
        normalized
        for normalized, page_numbers in page_occurrences.items()
        if len(page_numbers) >= threshold
    }
    remove_by_page: DefaultDict[int, Set[str]] = defaultdict(set)
    for page in document.pages:
        for block in page.blocks:
            if _is_margin_block(block, page.height):
                for line in block.text.splitlines():
                    normalized = _normalize_line(line)
                    if normalized in repeated:
                        remove_by_page[page.page_number].add(normalized)
    return dict(remove_by_page)


def _clean_block(
    block: TextBlock,
    page_height: float,
    removable_lines: Set[str],
    removed_lines: Set[str],
) -> str:
    normalized_text = unicodedata.normalize("NFC", block.text)
    normalized_text = normalized_text.replace("\r\n", "\n").replace("\r", "\n")
    normalized_text = _CONTROL_CHARACTERS.sub("", normalized_text)
    lines = normalized_text.split("\n")
    if _is_margin_block(block, page_height):
        kept_lines = []
        for line in lines:
            normalized = _normalize_line(line)
            if normalized and normalized in removable_lines:
                removed_lines.add(line.strip())
            else:
                kept_lines.append(line)
        normalized_text = "\n".join(kept_lines)
    normalized_text = "\n".join(line.rstrip() for line in normalized_text.split("\n"))
    return normalized_text.strip()


def _append_warning(warnings: List[str], warning: str) -> None:
    prefix = warning.split(":", 1)[0]
    if not any(existing.startswith(prefix) for existing in warnings):
        warnings.append(warning)


def clean_document(document: ExtractedDocument) -> ExtractedDocument:
    """Conservatively remove repeated PDF margin artifacts and control characters."""
    remove_by_page = _repeated_margin_lines(document)
    removed_lines: Set[str] = set()
    cleaned_pages: List[str] = []

    for page in document.pages:
        page_blocks = []
        for block in page.blocks:
            text = _clean_block(
                block,
                page.height,
                remove_by_page.get(page.page_number, set()),
                removed_lines,
            )
            if text:
                page_blocks.append(text)
        if page_blocks:
            cleaned_pages.append("\n\n".join(page_blocks))

    cleaned_text = re.sub(r"\n{3,}", "\n\n", "\n\n".join(cleaned_pages)).strip()
    raw_text = document.raw_text
    removed_repeated_lines = sorted(removed_lines)
    raw_char_count = len(raw_text)
    cleaned_char_count = len(cleaned_text)
    removed_char_count = max(0, raw_char_count - cleaned_char_count)
    reduction_ratio = (
        removed_char_count / raw_char_count if raw_char_count else 0.0
    )
    warnings = list(document.warnings)

    if not cleaned_text:
        _append_warning(warnings, "CLEANED_TEXT_EMPTY")
        if document.file_type == "pdf":
            _append_warning(
                warnings,
                "OCR_REQUIRED: Không trích xuất được văn bản. "
                "File có thể là PDF scan hoặc không chứa text.",
            )
    elif reduction_ratio >= 0.4:
        _append_warning(
            warnings,
            "HIGH_TEXT_REDUCTION: Nội dung sạch ngắn hơn nội dung gốc "
            "ít nhất 40%; cần kiểm tra thủ công.",
        )

    if raw_char_count and cleaned_char_count < 100:
        _append_warning(
            warnings,
            "LOW_TEXT_VOLUME: Văn bản trích xuất rất ngắn; cần kiểm tra thủ công.",
        )

    document.cleaned_text = cleaned_text
    document.removed_repeated_lines = removed_repeated_lines
    document.cleaning_stats = {
        "raw_char_count": raw_char_count,
        "cleaned_char_count": cleaned_char_count,
        "removed_char_count": removed_char_count,
        "reduction_ratio": round(reduction_ratio, 4),
        "removed_repeated_line_count": len(removed_repeated_lines),
    }
    document.warnings = warnings
    return document
