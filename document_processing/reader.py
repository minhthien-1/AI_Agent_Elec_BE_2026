from pathlib import Path
from typing import Callable, Union

from document_processing.models import ExtractedDocument
from document_processing.readers import read_docx, read_html, read_pdf, read_txt


READERS: dict[str, Callable[[Union[str, Path]], ExtractedDocument]] = {
    ".pdf": read_pdf,
    ".docx": read_docx,
    ".html": read_html,
    ".htm": read_html,
    ".txt": read_txt,
}


def read_document(file_path: Union[str, Path]) -> ExtractedDocument:
    path = Path(file_path).expanduser()
    reader = READERS.get(path.suffix.lower())
    if reader is None:
        raise ValueError(f"Định dạng tài liệu không được hỗ trợ: {path.suffix}")
    return reader(path)
