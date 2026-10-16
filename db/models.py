from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from db.database import Base


class Trace(Base):
    __tablename__ = "traces"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="running",
    )

    total_ms: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    steps: Mapped[List["TraceStep"]] = relationship(
        back_populates="trace",
        cascade="all, delete-orphan",
        order_by="TraceStep.step_order",
    )


class TraceStep(Base):
    __tablename__ = "trace_steps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    trace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "traces.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    step_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    step_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    input_data: Mapped[Any] = mapped_column(
        "input",
        JSONB,
        nullable=True,
    )

    output_data: Mapped[Any] = mapped_column(
        "output",
        JSONB,
        nullable=True,
    )

    duration_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    trace: Mapped["Trace"] = relationship(
        back_populates="steps",
    )

    __table_args__ = (
        Index(
            "ix_trace_steps_trace_order",
            "trace_id",
            "step_order",
        ),
    )


class Chunk(Base):
    """A document passage and its normalized multilingual-e5 embedding."""

    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    chunk_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[List[float]] = mapped_column(Vector(384), nullable=False)
    # ``metadata`` is reserved by SQLAlchemy's declarative base, so the Python
    # attribute has a different name while the database column remains metadata.
    metadata_json: Mapped[Any] = mapped_column("metadata", JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
