import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Recommendation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "recommendations"

    stock_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(10), nullable=False)  # BUY, SELL, HOLD
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    data_snapshot: Mapped[Optional[dict]] = mapped_column(JSON)
    model_version: Mapped[Optional[str]] = mapped_column(String(50))

    stock = relationship("Stock", back_populates="recommendations")
    user = relationship("User", back_populates="recommendations")
