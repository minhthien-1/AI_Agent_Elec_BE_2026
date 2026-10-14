from pathlib import Path
from typing import List, Union

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from document_processing.models import (
    ExtractedDocument,
    ExtractedPage,
    TextBlock,
)


def read_docx(file_path: Union[str, Path]) -> ExtractedDocument:
    path = Path(file_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {path}")
    if not path.is_file():
        raise ValueError(f"Đường dẫn không phải file: {path}")
    if path.suffix.lower() != ".docx":
        raise ValueError(f"Định dạng không phải DOCX: {path.name}")
    if path.stat().st_size == 0:
        raise ValueError(f"File rỗng: {path.name}")

    try:
        document = Document(str(path))
    except Exception as exc:
        raise RuntimeError(
            f"Không thể mở DOCX '{path.name}': {exc}"
        ) from exc

    blocks: List[TextBlock] = []
    block_index = 0
    body = document.element.body
    parent = document._body

    for child in body.iterchildren():
        if child.tag.endswith("}p"):
            paragraph = Paragraph(child, parent)
            text = paragraph.text.strip()
            if not text:
                continue
            block_index += 1
            style_name = paragraph.style.name if paragraph.style else ""
            kind = (
                "heading"
                if style_name.lower().startswith("heading")
                else "paragraph"
            )
            blocks.append(
                TextBlock(
                    page_number=1,
                    block_index=block_index,
                    text=text,
                    kind=kind,
                    metadata={"style": style_name} if style_name else {},
                )
            )
        elif child.tag.endswith("}tbl"):
            table = Table(child, parent)
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                if not any(cells):
                    continue
                block_index += 1
                blocks.append(
                    TextBlock(
                        page_number=1,
                        block_index=block_index,
                        text=" | ".join(cells),
                        kind="table_row",
                    )
                )

    properties = document.core_properties
    metadata = {
        key: value
        for key, value in {
            "title": properties.title,
            "subject": properties.subject,
            "author": properties.author,
        }.items()
        if value
    }

    return ExtractedDocument(
        source_path=str(path.resolve()),
        filename=path.name,
        file_type="docx",
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
