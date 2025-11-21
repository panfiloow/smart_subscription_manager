from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from decimal import Decimal

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")

    payment_date: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="subscriptions")
