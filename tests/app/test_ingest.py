import json

from app.rag import ingest


def test_ingest_reports_index_counts_and_elapsed_time(monkeypatch) -> None:
    monkeypatch.setattr(
        ingest, "index_documents", lambda input_path, batch_size: {"files": 30, "chunks": 123}
    )
    timestamps = iter((10.0, 12.345))
    monkeypatch.setattr(ingest.time, "perf_counter", lambda: next(timestamps))

    assert ingest.ingest("data/manuals", batch_size=16) == {
        "files": 30,
        "chunks": 123,
        "duration_seconds": 2.35,
    }


def test_main_prints_json_summary(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        ingest,
        "ingest",
        lambda input_path, batch_size: {
            "files": 30,
            "chunks": 456,
            "duration_seconds": 8.2,
        },
    )

    assert ingest.main(["data/manuals"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "files": 30,
        "chunks": 456,
        "duration_seconds": 8.2,
    }
