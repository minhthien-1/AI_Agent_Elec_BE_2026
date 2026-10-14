from document_processing.cleaner import clean_document
from document_processing.models import ExtractedDocument, ExtractedPage, TextBlock


def test_cleaner_removes_repeated_pdf_margin_artifacts() -> None:
    pages = [
        ExtractedPage(
            page_number=page_number,
            width=300,
            height=400,
            blocks=[
                TextBlock(
                    page_number=page_number,
                    block_index=1,
                    text="REPEATED HEADER",
                    bbox=(20, 10, 200, 30),
                ),
                TextBlock(
                    page_number=page_number,
                    block_index=2,
                    text=f"Unique content {page_number}.",
                    bbox=(20, 100, 200, 140),
                ),
                TextBlock(
                    page_number=page_number,
                    block_index=3,
                    text="REPEATED FOOTER",
                    bbox=(20, 370, 200, 390),
                ),
            ],
        )
        for page_number in range(1, 5)
    ]
    document = ExtractedDocument(
        source_path="manual.pdf",
        filename="manual.pdf",
        file_type="pdf",
        page_count=4,
        pages=pages,
    )

    cleaned = clean_document(document)

    assert "REPEATED HEADER" not in cleaned.cleaned_text
    assert "REPEATED FOOTER" not in cleaned.cleaned_text
    assert all(f"Unique content {page}." in cleaned.cleaned_text for page in range(1, 5))
    assert cleaned.removed_repeated_lines == ["REPEATED FOOTER", "REPEATED HEADER"]
    assert cleaned.cleaning_stats["removed_repeated_line_count"] == 2


def test_cleaner_preserves_technical_symbols_and_removes_controls() -> None:
    block = TextBlock(
        page_number=1,
        block_index=1,
        text="Điện áp\x00 220 V; nhiệt độ 4 °C; ± Ω →",
    )
    document = ExtractedDocument(
        source_path="guide.txt",
        filename="guide.txt",
        file_type="txt",
        page_count=1,
        pages=[ExtractedPage(1, 0, 0, [block])],
    )

    cleaned = clean_document(document)

    assert cleaned.cleaned_text == "Điện áp 220 V; nhiệt độ 4 °C; ± Ω →"


def test_cleaner_warns_when_large_amount_of_text_disappears() -> None:
    pages = [
        ExtractedPage(
            page_number=page_number,
            width=300,
            height=400,
            blocks=[
                TextBlock(
                    page_number=page_number,
                    block_index=1,
                    text="VERY LONG REPEATED HEADER " * 20,
                    bbox=(20, 10, 280, 30),
                ),
                TextBlock(
                    page_number=page_number,
                    block_index=2,
                    text=f"Body {page_number}",
                    bbox=(20, 150, 280, 180),
                ),
            ],
        )
        for page_number in (1, 2)
    ]
    document = ExtractedDocument(
        source_path="artifact.pdf",
        filename="artifact.pdf",
        file_type="pdf",
        page_count=2,
        pages=pages,
    )

    cleaned = clean_document(document)

    assert any(warning.startswith("HIGH_TEXT_REDUCTION") for warning in cleaned.warnings)
