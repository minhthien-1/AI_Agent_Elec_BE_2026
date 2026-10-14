from pathlib import Path
from typing import Union

from document_processing.models import (
    ExtractedDocument,
    ExtractedPage,
    TextBlock,
)


def _decode_text(data: bytes) -> tuple[str, str, bool]:
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig"), "utf-8-sig", False
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16"), "utf-16", False
    try:
        return data.decode("utf-8"), "utf-8", False
    except UnicodeDecodeError:
        return data.decode("cp1258"), "cp1258", True


def read_txt(file_path: Union[str, Path]) -> ExtractedDocument:
    path = Path(file_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {path}")
    if not path.is_file():
        raise ValueError(f"Đường dẫn không phải file: {path}")
    if path.suffix.lower() != ".txt":
        raise ValueError(f"Định dạng không phải TXT: {path.name}")
    if path.stat().st_size == 0:
        raise ValueError(f"File rỗng: {path.name}")

    try:
        text, encoding, used_fallback = _decode_text(path.read_bytes())
    except (OSError, UnicodeDecodeError) as exc:
        raise RuntimeError(
            f"Không thể giải mã TXT '{path.name}': {exc}"
        ) from exc

    blocks = (
        [
            TextBlock(
                page_number=1,
                block_index=1,
                text=text,
                kind="text",
            )
        ]
        if text
        else []
    )
    warnings = [f"ENCODING_FALLBACK: Đã giải mã bằng {encoding}."] if used_fallback else []

    return ExtractedDocument(
        source_path=str(path.resolve()),
        filename=path.name,
        file_type="txt",
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
        warnings=warnings,
        metadata={"encoding": encoding},
    )
