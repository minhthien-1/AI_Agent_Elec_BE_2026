from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from infrastructure.persistence.models import Trace, TraceStep


class TraceService:
    """Persist trace records for application use cases."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def start_trace(self) -> uuid.UUID:
        trace = Trace(
            id=uuid.uuid4(),
            status="running",
        )

        trace_id = trace.id
        self.db.add(trace)
        self._commit()
        return trace_id

    def add_step(
        self,
        trace_id: uuid.UUID,
        step_order: int,
        step_name: str,
        input_data: Any = None,
        output_data: Any = None,
        duration_ms: float = 0.0,
    ) -> None:
        step = TraceStep(
            trace_id=trace_id,
            step_order=step_order,
            step_name=step_name,
            input_data=input_data,
            output_data=output_data,
            duration_ms=duration_ms,
        )

        self.db.add(step)
        self._commit()

    def finish_trace(
        self,
        trace_id: uuid.UUID,
        total_ms: float,
    ) -> None:
        trace = self._get_trace(trace_id)
        trace.total_ms = total_ms
        trace.status = "success"
        self._commit()

    def fail_trace(
        self,
        trace_id: uuid.UUID,
        total_ms: float,
    ) -> None:
        trace = self._get_trace(trace_id)
        trace.total_ms = total_ms
        trace.status = "failed"
        self._commit()

    def _get_trace(self, trace_id: uuid.UUID) -> Trace:
        trace = self.db.get(Trace, trace_id)
        if trace is None:
            raise LookupError(f"Trace not found: {trace_id}")
        return trace

    def _commit(self) -> None:
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise