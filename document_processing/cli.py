import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from document_processing.cleaner import clean_document
from document_processing.reader import READERS, read_document


SUPPORTED_SUFFIXES = set(READERS)


def _discover_inputs(input_path: Path, output_path: Path) -> List[Path]:
    if not input_path.exists():
        raise FileNotFoundError(f"Không tìm thấy input: {input_path}")
    if input_path.is_file():
        if input_path.suffix.lower() not in SUPPORTED_SUFFIXES:
            raise ValueError(f"Định dạng không được hỗ trợ: {input_path.suffix}")
        return [input_path]
    if not input_path.is_dir():
        raise ValueError(f"Input không phải file hoặc thư mục: {input_path}")
    if input_path.resolve() == output_path.resolve():
        raise ValueError("Thư mục output không được trùng với thư mục input.")

    files = []
    output_resolved = output_path.resolve()
    for path in sorted(input_path.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        try:
            path.resolve().relative_to(output_resolved)
        except ValueError:
            files.append(path)
    return files


def _output_paths(
    source: Path,
    input_path: Path,
    output_path: Path,
) -> Tuple[Path, Path]:
    if input_path.is_dir():
        relative = source.relative_to(input_path)
        target_stem = output_path / relative.parent / relative.stem
    else:
        target_stem = output_path / source.stem
    return target_stem.with_suffix(".txt"), target_stem.with_suffix(".json")


def process_inputs(input_value: str, output_value: str) -> Tuple[dict, List[str]]:
    input_path = Path(input_value).expanduser()
    output_path = Path(output_value).expanduser()
    files = _discover_inputs(input_path, output_path)
    failures: List[str] = []
    warning_count = 0
    processed = 0

    for source in files:
        try:
            document = clean_document(read_document(source))
            text_path, json_path = _output_paths(source, input_path, output_path)
            if source.resolve() in {text_path.resolve(), json_path.resolve()}:
                raise ValueError(f"Output sẽ ghi đè file nguồn: {source}")
            text_path.parent.mkdir(parents=True, exist_ok=True)
            text_path.write_text(document.cleaned_text, encoding="utf-8")
            payload = asdict(document)
            payload["raw_text"] = document.raw_text
            payload["char_count"] = document.char_count
            json_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            processed += 1
            warning_count += len(document.warnings)
        except (OSError, RuntimeError, ValueError, UnicodeError) as exc:
            failures.append(f"{source}: {exc}")

    return (
        {
            "discovered": len(files),
            "processed": processed,
            "failed": len(failures),
            "warning_count": warning_count,
        },
        failures,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Đọc, làm sạch và xuất tài liệu PDF/DOCX/HTML/TXT."
    )
    parser.add_argument("--input", required=True, help="File hoặc thư mục nguồn.")
    parser.add_argument("--output", required=True, help="Thư mục chứa output.")
    args = parser.parse_args(argv)

    try:
        summary, failures = process_inputs(args.input, args.output)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
        return 2

    print(json.dumps(summary, ensure_ascii=False))
    for failure in failures:
        print(f"FAILED: {failure}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
