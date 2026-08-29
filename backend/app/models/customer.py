from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    customer_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    segment: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    lifetime_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    orders_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    successful_payments: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    failed_payments: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    previous_recovery_success: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    contact_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )