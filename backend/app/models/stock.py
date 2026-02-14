from __future__ import annotations

import uuid
from datetime import date as date_type
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Stock(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "stocks"

    symbol: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    exchange: Mapped[Optional[str]] = mapped_column(String(50))
    asset_type: Mapped[str] = mapped_column(String(20), default="stock")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    holdings = relationship("Holding", back_populates="stock")
    price_history = relationship("PriceHistory", back_populates="stock", cascade="all, delete-orphan")
    latest_price = relationship("LatestPrice", back_populates="stock", uselist=False, cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="stock")
    news_associations = relationship("NewsArticleStock", back_populates="stock")


class PriceHistory(UUIDMixin, Base):
    __tablename__ = "price_history"
    __table_args__ = (UniqueConstraint("stock_id", "date", name="uq_price_history_stock_date"),)

    stock_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    volume: Mapped[int] = mapped_column(nullable=False)
    vwap: Mapped[Optional[Decimal]] = mapped_column(Numeric(19, 4))

    stock = relationship("Stock", back_populates="price_history")


class LatestPrice(UUIDMixin, Base):
    __tablename__ = "latest_prices"

    stock_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stocks.id"), unique=True, nullable=False
    )
    price: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    previous_close: Mapped[Optional[Decimal]] = mapped_column(Numeric(19, 4))
    change_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    stock = relationship("Stock", back_populates="latest_price")
