from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from db.models import Trace, TraceStep


class TraceService:

    def start_trace(
        self,
        db: Session,
    ) -> Trace:

        trace = Trace(
            id=uuid.uuid4(),
            status="running",
        )

        db.add(trace)
        db.commit()
        db.refresh(trace)

        return trace

    def add_step(
        self,
        db: Session,
        trace_id: uuid.UUID,
        step_order: int,
        step_name: str,
        input_data: Any = None,
        output_data: Any = None,
        duration_ms: float = 0.0,
    ) -> TraceStep:

        step = TraceStep(
            trace_id=trace_id,
            step_order=step_order,
            step_name=step_name,
            input_data=input_data,
            output_data=output_data,
            duration_ms=duration_ms,
        )

        db.add(step)
        db.commit()
        db.refresh(step)

        return step

    def finish_trace(
        self,
        db: Session,
        trace: Trace,
        total_ms: float,
    ) -> Trace:

        trace.total_ms = total_ms
        trace.status = "success"

        db.commit()
        db.refresh(trace)

        return trace

    def fail_trace(
        self,
        db: Session,
        trace: Trace,
        total_ms: float,
    ) -> Trace:

        trace.total_ms = total_ms
        trace.status = "failed"

        db.commit()
        db.refresh(trace)

        return trace