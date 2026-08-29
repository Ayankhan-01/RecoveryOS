from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RecoveryEvent(Base):
    __tablename__ = "recovery_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.id"),
        nullable=False,
    )

    action: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    predicted_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    expected_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    executed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    outcome: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    recovered_amount: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    intervention_cost: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )