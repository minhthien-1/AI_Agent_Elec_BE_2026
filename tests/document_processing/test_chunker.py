from document_processing.chunker import chunk_document
from document_processing.models import ExtractedDocument


def _document(text: str, **kwargs: str) -> ExtractedDocument:
    return ExtractedDocument(
        source_path=kwargs.get(
            "source_path", "data/manuals/files/manuals/washing_machines/M001_samsung_manual.pdf"
        ),
        filename=kwargs.get("filename", "M001_samsung_manual.pdf"),
        file_type="pdf",
        page_count=1,
        cleaned_text=text,
    )


def test_chunker_splits_at_headings_and_keeps_required_metadata() -> None:
    document = _document(
        "# An toàn\nRút điện trước khi vệ sinh.\n\n# Lắp đặt\nĐặt máy trên mặt phẳng."
    )

    chunks = chunk_document(document)

    assert [chunk.text for chunk in chunks] == [
        "An toàn\n\nRút điện trước khi vệ sinh.",
        "Lắp đặt\n\nĐặt máy trên mặt phẳng.",
    ]
    assert chunks[0].metadata == {
        "device": "washing_machine",
        "brand": "samsung",
        "section": "An toàn",
    }
    assert chunks[1].metadata["section"] == "Lắp đặt"


def test_chunker_splits_long_section_with_exact_overlap() -> None:
    words = [f"w{index}" for index in range(550)]
    chunks = chunk_document(
        _document("# Vận hành\n" + " ".join(words)),
        max_tokens=500,
        overlap_tokens=50,
    )

    assert [chunk.token_count for chunk in chunks] == [500, 100]
    first_body = chunks[0].text.split("\n\n", 1)[1].split()
    second_body = chunks[1].text.split("\n\n", 1)[1].split()
    assert first_body[-50:] == second_body[:50]
    assert all(chunk.token_count <= 500 for chunk in chunks)


def test_explicit_metadata_overrides_inference() -> None:
    chunks = chunk_document(
        _document("# Bảo trì\nNội dung."), device="water_heater", brand="acme"
    )

    assert chunks[0].metadata["device"] == "water_heater"
    assert chunks[0].metadata["brand"] == "acme"


def test_chunker_inferrs_rice_cooker_metadata_from_source_path() -> None:
    chunks = chunk_document(
        _document(
            "# Vận hành\nNội dung.",
            source_path="data/manuals/files/manuals/rice_cookers/M002_panasonic_manual.pdf",
            filename="M002_panasonic_manual.pdf",
        )
    )

    assert chunks[0].metadata["device"] == "rice_cooker"
    assert chunks[0].metadata["brand"] == "panasonic"
