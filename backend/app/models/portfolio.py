import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Portfolio(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "portfolios"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000))

    user = relationship("User", back_populates="portfolios")
    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")


class Holding(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "holdings"
    __table_args__ = (UniqueConstraint("portfolio_id", "stock_id", name="uq_holding_portfolio_stock"),)

    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False
    )
    stock_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    avg_cost_basis: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)

    portfolio = relationship("Portfolio", back_populates="holdings")
    stock = relationship("Stock", back_populates="holdings")
