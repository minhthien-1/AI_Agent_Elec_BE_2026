from pathlib import Path
from typing import List, Union

from bs4 import BeautifulSoup

from document_processing.models import (
    ExtractedDocument,
    ExtractedPage,
    TextBlock,
)


def read_html(file_path: Union[str, Path]) -> ExtractedDocument:
    path = Path(file_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {path}")
    if not path.is_file():
        raise ValueError(f"Đường dẫn không phải file: {path}")
    if path.suffix.lower() not in {".html", ".htm"}:
        raise ValueError(f"Định dạng không phải HTML: {path.name}")
    if path.stat().st_size == 0:
        raise ValueError(f"File rỗng: {path.name}")

    try:
        soup = BeautifulSoup(path.read_bytes(), "html.parser")
    except OSError as exc:
        raise RuntimeError(
            f"Không thể đọc HTML '{path.name}': {exc}"
        ) from exc

    for element in soup(["script", "style", "noscript", "template"]):
        element.decompose()

    blocks: List[TextBlock] = []
    selectors = "h1, h2, h3, h4, h5, h6, p, li, th, td"
    for element in soup.select(selectors):
        if element.find_parent(
            ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "th", "td"]
        ):
            continue
        text = " ".join(element.stripped_strings)
        if not text:
            continue
        kind = "heading" if element.name.startswith("h") else element.name
        blocks.append(
            TextBlock(
                page_number=1,
                block_index=len(blocks) + 1,
                text=text,
                kind=kind,
                metadata={"level": element.name[1:]} if kind == "heading" else {},
            )
        )

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    metadata = {"title": title} if title else {}
    if soup.original_encoding:
        metadata["encoding"] = soup.original_encoding

    return ExtractedDocument(
        source_path=str(path.resolve()),
        filename=path.name,
        file_type="html",
        page_count=1,
        pages=[
            ExtractedPage(
                page_number=1,
                width=0.0,
                height=0.0,
                blocks=blocks,
                metadata={"pagination": "logical_document"},
            )
        ],
        metadata=metadata,
    )
