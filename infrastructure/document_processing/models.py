from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


Metadata = Dict[str, Any]


@dataclass(frozen=True)
class TextBlock:
    """Một block văn bản được trích xuất từ tài liệu."""

    page_number: int
    block_index: int
    text: str
    bbox: Optional[Tuple[float, float, float, float]] = None
    kind: str = "text"
    metadata: Metadata = field(default_factory=dict)


@dataclass
class ExtractedPage:
    """Nội dung trích xuất của một trang."""

    page_number: int
    width: float
    height: float
    blocks: List[TextBlock] = field(default_factory=list)
    metadata: Metadata = field(default_factory=dict)

    @property
    def raw_text(self) -> str:
        return "\n\n".join(
            block.text for block in self.blocks if block.text.strip()
        )


@dataclass
class ExtractedDocument:
    """Kết quả đọc tài liệu trước khi làm sạch."""

    source_path: str
    filename: str
    file_type: str
    page_count: int
    pages: List[ExtractedPage] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Metadata = field(default_factory=dict)
    cleaned_text: str = ""
    removed_repeated_lines: List[str] = field(default_factory=list)
    cleaning_stats: Metadata = field(default_factory=dict)

    @property
    def raw_text(self) -> str:
        """Toàn bộ văn bản, ghép theo thứ tự trang."""
        return "\n\n".join(
            page.raw_text for page in self.pages if page.raw_text.strip()
        )

    @property
    def char_count(self) -> int:
        return len(self.raw_text)


@dataclass(frozen=True)
class DocumentChunk:
    """Một đoạn văn bản sẵn sàng đưa vào bước embedding hoặc retrieval."""

    chunk_id: str
    text: str
    token_count: int
    metadata: Metadata = field(default_factory=dict)
