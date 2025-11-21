from typing import TYPE_CHECKING, List
from datetime import datetime
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, DateTime, func
from app.db.base import Base
import uuid

if TYPE_CHECKING:
    from app.models.subscription import Subscription


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(280), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    subscriptions: Mapped[List["Subscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
