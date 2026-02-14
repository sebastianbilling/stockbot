import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class NewsArticle(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "news_articles"

    external_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    headline: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    url: Mapped[Optional[str]] = mapped_column(String(1000))
    source: Mapped[Optional[str]] = mapped_column(String(100))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    stock_associations = relationship("NewsArticleStock", back_populates="news_article", cascade="all, delete-orphan")


class NewsArticleStock(Base):
    __tablename__ = "news_article_stocks"

    news_article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("news_articles.id"), primary_key=True
    )
    stock_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stocks.id"), primary_key=True
    )

    news_article = relationship("NewsArticle", back_populates="stock_associations")
    stock = relationship("Stock", back_populates="news_associations")
