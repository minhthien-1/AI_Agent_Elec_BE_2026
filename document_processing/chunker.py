"""Chia tài liệu đã làm sạch thành các đoạn nhỏ, có ngữ cảnh mục."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

from document_processing.models import DocumentChunk, ExtractedDocument


DEFAULT_MAX_TOKENS = 500
DEFAULT_OVERLAP_TOKENS = 50
UNKNOWN_SECTION = "Không có tiêu đề"
_TOKEN_PATTERN = re.compile(r"\S+")
_NUMBERED_HEADING = re.compile(r"^\s*(?:\d+(?:\.\d+)*[.)]|[IVXLC]+[.)])\s+\S+", re.IGNORECASE)
_MARKDOWN_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
_KNOWN_BRANDS = ("ariston", "lg", "panasonic", "samsung", "toshiba", "evn")
_DEVICE_BY_PATH_PART = {
    "air_conditioners": "air_conditioner",
    "freezers": "freezer",
    "refrigerators": "refrigerator",
    "washing_machines": "washing_machine",
}


def chunk_document(
    document: ExtractedDocument,
    *,
    device: Optional[str] = None,
    brand: Optional[str] = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> List[DocumentChunk]:
    """Chia theo tiêu đề trước, rồi mới cắt mục dài theo giới hạn token.

    Token ở đây là một chuỗi không có khoảng trắng. Cách đếm này cố ý không
    phụ thuộc tokenizer của một model cụ thể; khi chọn model embedding/LLM mới,
    có thể thay hàm :func:`_tokens` bằng tokenizer tương ứng.
    """
    _validate_limits(max_tokens, overlap_tokens)
    text = document.cleaned_text or document.raw_text
    if not text.strip():
        return []

    resolved_device = device or document.metadata.get("device") or _infer_device(document)
    resolved_brand = brand or document.metadata.get("brand") or _infer_brand(document)
    source_stem = Path(document.filename).stem
    chunks: List[DocumentChunk] = []

    for section_index, (section, section_text) in enumerate(_split_sections(text)):
        for part_index, part_tokens in enumerate(
            _split_tokens(_tokens(section_text), max_tokens, overlap_tokens)
        ):
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{source_stem}:{section_index}:{part_index}",
                    text=" ".join(part_tokens),
                    token_count=len(part_tokens),
                    metadata={
                        "device": resolved_device,
                        "brand": resolved_brand,
                        "section": section,
                    },
                )
            )
    return chunks


def _validate_limits(max_tokens: int, overlap_tokens: int) -> None:
    if max_tokens <= 0:
        raise ValueError("max_tokens phải lớn hơn 0.")
    if overlap_tokens < 0 or overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens phải từ 0 đến nhỏ hơn max_tokens.")


def _split_sections(text: str) -> Iterator[Tuple[str, str]]:
    section = UNKNOWN_SECTION
    lines: List[str] = []
    for line in text.splitlines():
        heading = _heading_text(line)
        if heading is not None:
            if _tokens("\n".join(lines)):
                yield section, "\n".join(lines)
            section = heading
            lines = []
        else:
            lines.append(line)
    if _tokens("\n".join(lines)):
        yield section, "\n".join(lines)


def _heading_text(line: str) -> Optional[str]:
    """Nhận diện heading tường minh và heading ngắn đứng độc lập."""
    stripped = line.strip()
    if not stripped:
        return None
    markdown = _MARKDOWN_HEADING.match(stripped)
    if markdown:
        return markdown.group(1).strip()
    if _NUMBERED_HEADING.match(stripped):
        return stripped

    words = _tokens(stripped)
    if (
        len(words) <= 12
        and len(stripped) <= 100
        and stripped[-1] not in ".!?;,:"
        and not any(character.isdigit() for character in stripped)
    ):
        return stripped
    return None


def _split_tokens(
    tokens: List[str], max_tokens: int, overlap_tokens: int
) -> Iterator[List[str]]:
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        yield tokens[start:end]
        if end == len(tokens):
            return
        start = end - overlap_tokens


def _tokens(text: str) -> List[str]:
    return _TOKEN_PATTERN.findall(text)


def _infer_brand(document: ExtractedDocument) -> str:
    filename = document.filename.lower()
    return next((brand for brand in _KNOWN_BRANDS if brand in filename), "unknown")


def _infer_device(document: ExtractedDocument) -> str:
    path_parts = [part.lower() for part in Path(document.source_path).parts]
    for path_part, device in _DEVICE_BY_PATH_PART.items():
        if path_part in path_parts:
            return device
    filename = document.filename.lower()
    for keyword, device in (
        ("washer", "washing_machine"),
        ("washing", "washing_machine"),
        ("fridge", "refrigerator"),
        ("refrigerator", "refrigerator"),
        ("freezer", "freezer"),
        ("heater", "water_heater"),
        ("ac_", "air_conditioner"),
    ):
        if keyword in filename:
            return device
    return "unknown"
