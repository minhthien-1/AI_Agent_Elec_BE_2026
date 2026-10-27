"""Export the top-k retrieved chunks for 20 manual relevance checks.

Run after PostgreSQL/pgvector is up and ``app.rag.ingest`` has indexed the
manuals.  The CSV output intentionally leaves ``relevant`` blank: a human
reviewer reads each returned chunk and enters 1 (relevant) or 0 (irrelevant).
"""

from __future__ import annotations

import csv
import argparse
import sys
from pathlib import Path
from typing import Sequence

# When executed as ``python eval/run_retrieval_manual_check.py``, Python adds
# ``eval/`` (not the repository root) to its import path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.retriever import PgvectorRetriever
from db.database import SessionLocal


TOP_K = 5
OUTPUT_PATH = Path("eval/output/manual_retrieval_check.csv")

# These IDs correspond to C-01..C-20 in the workbook supplied for this project.
TEST_CASES = [
    ("C-01", "Máy giặt Toshiba vắt rất ồn và rung mạnh, tôi cần kiểm tra gì trước?", "T001_toshiba_washer_noise.pdf"),
    ("C-02", "Tôi nên vệ sinh và bảo dưỡng máy giặt Toshiba như thế nào để dùng bền hơn?", "T002_toshiba_washer_maintenance.pdf"),
    ("C-03", "Tủ lạnh Toshiba nhà tôi phát ra tiếng kêu lạ, trường hợp nào là bình thường?", "T003_toshiba_fridge_noise.pdf"),
    ("C-04", "Tủ lạnh Toshiba nên bảo dưỡng định kỳ những gì?", "T004_toshiba_fridge_maintenance.pdf"),
    ("C-05", "Tủ lạnh Toshiba không chạy hoặc không lạnh thì tôi nên kiểm tra thứ tự nào?", "T005_toshiba_fridge_not_working.pdf"),
    ("C-06", "Điều hòa Toshiba có tiếng nước chảy và mùi lúc mới bật, có bình thường không?", "T006_toshiba_ac_normal_behaviors.pdf"),
    ("C-07", "Bao lâu thì nên vệ sinh, bảo dưỡng điều hòa Toshiba và cần làm những gì?", "T007_toshiba_ac_maintenance.pdf"),
    ("C-08", "Bình nóng lạnh Ariston không nóng dù đèn báo vẫn sáng, nguyên nhân nào cần kiểm tra?", "T009_ariston_water_heater_not_heating.pdf"),
    ("C-09", "Bình nóng lạnh Ariston nước nóng quá mức bất thường, tôi phải xử lý ra sao?", "T010_ariston_water_heater_overheating.pdf"),
    ("C-10", "Bình nóng lạnh Ariston cần bảo dưỡng định kỳ thế nào?", "T008_ariston_water_heater_maintenance.pdf"),
    ("C-11", "Dùng bình nóng lạnh trực tiếp Ariston cần lưu ý an toàn điện gì?", "T011_ariston_instant_heater_safety.pdf"),
    ("C-12", "Bình nóng lạnh Ariston của tôi hay bị lỗi vặt, những lỗi thường gặp là gì?", "T012_ariston_water_heater_common_faults.pdf"),
    ("C-13", "Bình nước nóng năng lượng mặt trời Ariston cần bảo dưỡng những hạng mục nào?", "T013_ariston_solar_heater_maintenance.pdf"),
    ("C-14", "Tủ lạnh Panasonic được bảo hành bao lâu nếu đã kích hoạt bảo hành điện tử?", "W001_panasonic_warranty_period_2026.pdf"),
    ("C-15", "Những trường hợp nào có thể không được Panasonic bảo hành?", "W002_panasonic_warranty_terms.pdf"),
    ("C-16", "Tủ lạnh Panasonic nên sử dụng như thế nào để tiết kiệm điện và bảo quản thực phẩm?", "G001_panasonic_fridge_usage_guide.pdf"),
    ("C-17", "Máy giặt Samsung WA14CG5886BDSV có lưu ý gì khi lắp đặt và sử dụng lần đầu?", "M001_samsung_WA14CG5886BDSV_manual_vi.pdf"),
    ("C-18", "Máy giặt LG FB1209D5W cần vệ sinh, sử dụng thế nào để tránh mùi và hoạt động ổn định?", "M009_lg_FB1209D5W_manual_vi.pdf"),
    ("C-19", "Tủ đông LG LOF16BGM mới mua cần lắp đặt và cài đặt thế nào?", "M006_lg_LOF16BGM_manual_vi.pdf"),
    ("C-20", "Điều hòa LG IDC09M1N có hướng dẫn vận hành và vệ sinh cơ bản nào cho người dùng?", "M005_lg_IDC09M1N_manual_vi.pdf"),
]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export top-k chunks for manual relevance review."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
        help=f"CSV path to write (default: {OUTPUT_PATH})",
    )
    args = parser.parse_args(argv)
    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    retriever = PgvectorRetriever()
    db = SessionLocal()

    try:
        with output_path.open("w", newline="", encoding="utf-8-sig") as output_file:
            writer = csv.DictWriter(
                output_file,
                fieldnames=(
                    "case_id",
                    "question",
                    "expected_source",
                    "rank",
                    "chunk_id",
                    "retrieved_source",
                    "page",
                    "score",
                    "chunk_content",
                    "relevant",
                    "review_note",
                ),
            )
            writer.writeheader()

            for case_id, question, expected_source in TEST_CASES:
                for rank, chunk in enumerate(retriever.retrieve(db, question, k=TOP_K), start=1):
                    writer.writerow(
                        {
                            "case_id": case_id,
                            "question": question,
                            "expected_source": expected_source,
                            "rank": rank,
                            "chunk_id": chunk.id,
                            "retrieved_source": chunk.metadata.get("source", ""),
                            "page": chunk.metadata.get("page", ""),
                            "score": f"{chunk.score:.4f}",
                            "chunk_content": chunk.content,
                            "relevant": "",
                            "review_note": "",
                        }
                    )
    finally:
        db.close()

    print(f"Wrote {output_path}")
    print("Review each row, enter 1 or 0 in relevant, then calculate Hit@5.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
