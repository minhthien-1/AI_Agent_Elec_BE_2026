import pytest

from infrastructure.persistence.models import Trace, TraceStep
from infrastructure.persistence.trace_service import TraceService


class FakeSession:
    def __init__(self) -> None:
        self.records = []
        self.commit_count = 0
        self.rollback_count = 0
        self.fail_commit = False

    def add(self, record) -> None:
        self.records.append(record)

    def commit(self) -> None:
        self.commit_count += 1
        if self.fail_commit:
            raise RuntimeError("database commit failed")

    def rollback(self) -> None:
        self.rollback_count += 1

    def get(self, model, record_id):
        return next(
            (
                record for record in self.records
                if isinstance(record, model) and record.id == record_id
            ),
            None,
        )


def test_trace_service_persists_trace_steps_and_status():
    db = FakeSession()
    trace_service = TraceService(db)

    trace_id = trace_service.start_trace()
    trace_service.add_step(
        trace_id=trace_id,
        step_order=1,
        step_name="generate",
        input_data={"message": "hello"},
        output_data={"answer": "world"},
        duration_ms=12.5,
    )
    trace_service.finish_trace(trace_id, total_ms=20.0)

    trace = db.get(Trace, trace_id)
    step = next(record for record in db.records if isinstance(record, TraceStep))
    assert trace.status == "success"
    assert trace.total_ms == 20.0
    assert step.trace_id == trace_id
    assert step.input_data == {"message": "hello"}
    assert step.output_data == {"answer": "world"}
    assert db.commit_count == 3


def test_trace_service_rolls_back_and_propagates_commit_failure():
    db = FakeSession()
    db.fail_commit = True
    trace_service = TraceService(db)

    with pytest.raises(RuntimeError, match="database commit failed"):
        trace_service.start_trace()

    assert db.rollback_count == 1
