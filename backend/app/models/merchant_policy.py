from datetime import datetime

from sqlalchemy import DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MerchantPolicy(Base):
    __tablename__ = "merchant_policies"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    max_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=2,
    )

    max_contacts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=2,
    )

    max_discount_percent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=5.00,
    )

    max_intervention_cost: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=10.00,
    )

    recovery_window_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=48,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )