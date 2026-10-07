import uuid

from db.database import SessionLocal
from db.models import Trace, TraceStep


def test_trace_and_trace_step():
    db = SessionLocal()

    trace = None

    try:
        trace = Trace(
            id=uuid.uuid4(),
            status="running",
        )

        db.add(trace)
        db.commit()
        db.refresh(trace)

        assert trace.id is not None
        assert trace.status == "running"

        step = TraceStep(
            trace_id=trace.id,
            step_order=1,
            step_name="test_step",
            input_data={
                "message": "hello"
            },
            output_data={
                "result": "world"
            },
            duration_ms=12.5,
        )

        db.add(step)
        db.commit()
        db.refresh(step)

        assert step.id is not None
        assert step.trace_id == trace.id
        assert step.step_order == 1
        assert step.step_name == "test_step"
        assert step.duration_ms == 12.5

        assert step.input_data == {
            "message": "hello"
        }

        assert step.output_data == {
            "result": "world"
        }

    finally:
        if trace is not None:
            existing_trace = db.get(
                Trace,
                trace.id,
            )

            if existing_trace is not None:
                db.delete(existing_trace)
                db.commit()

        db.close()