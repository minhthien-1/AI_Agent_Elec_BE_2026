from pathlib import Path
from typing import List, Union

import pymupdf

from document_processing.models import (
    ExtractedDocument,
    ExtractedPage,
    TextBlock,
)


def read_pdf(file_path: Union[str, Path]) -> ExtractedDocument:
    """
    Đọc văn bản từ PDF và trả về cấu trúc dữ liệu thống nhất.

    Chưa loại header/footer, số trang hoặc chuẩn hóa nội dung.
    """

    path = Path(file_path).expanduser()

    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {path}")

    if not path.is_file():
        raise ValueError(f"Đường dẫn không phải file: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Định dạng không phải PDF: {path.name}")

    if path.stat().st_size == 0:
        raise ValueError(f"File rỗng: {path.name}")

    try:
        pdf = pymupdf.open(str(path))
    except Exception as exc:
        raise RuntimeError(
            f"Không thể mở PDF '{path.name}': {exc}"
        ) from exc

    pages: List[ExtractedPage] = []
    warnings: List[str] = []
    metadata = {}

    with pdf:
        if pdf.needs_pass:
            raise ValueError(
                f"PDF yêu cầu mật khẩu, chưa thể đọc: {path.name}"
            )
        metadata = {
            key: value
            for key, value in (pdf.metadata or {}).items()
            if value is not None
        }

        for page_number, page in enumerate(pdf, start=1):
            blocks: List[TextBlock] = []

            # sort=True yêu cầu sắp xếp block theo thứ tự đọc gần đúng.
            extracted_blocks = page.get_text("blocks", sort=True)

            for block_index, block in enumerate(
                extracted_blocks, start=1
            ):
                # Các block văn bản thường có tọa độ ở 4 phần tử đầu,
                # nội dung văn bản ở phần tử thứ 5.
                if len(block) < 5:
                    continue

                text = block[4]

                if not isinstance(text, str) or not text.strip():
                    continue

                bbox = (
                    float(block[0]),
                    float(block[1]),
                    float(block[2]),
                    float(block[3]),
                )

                blocks.append(
                    TextBlock(
                        page_number=page_number,
                        block_index=block_index,
                        text=text.strip(),
                        bbox=bbox,
                        kind="text",
                    )
                )

            pages.append(
                ExtractedPage(
                    page_number=page_number,
                    width=float(page.rect.width),
                    height=float(page.rect.height),
                    blocks=blocks,
                    metadata={"rotation": int(page.rotation)},
                )
            )

    pages_without_text = [
        page.page_number for page in pages if not page.blocks
    ]

    if pages_without_text:
        warnings.append(
            "PAGES_WITHOUT_EXTRACTABLE_TEXT: "
            + ", ".join(map(str, pages_without_text))
        )

    document = ExtractedDocument(
        source_path=str(path.resolve()),
        filename=path.name,
        file_type="pdf",
        page_count=len(pages),
        pages=pages,
        warnings=warnings,
        metadata=metadata,
    )

    if not document.raw_text.strip():
        document.warnings.append(
            "OCR_REQUIRED: Không trích xuất được văn bản. "
            "File có thể là PDF scan hoặc không chứa text."
        )

    elif document.char_count < 100:
        document.warnings.append(
            "LOW_TEXT_VOLUME: Văn bản trích xuất rất ngắn; "
            "cần kiểm tra thủ công."
        )

    return document