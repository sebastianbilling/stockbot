import json
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

import anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.notification import Notification
from app.models.recommendation import Recommendation
from app.models.stock import PriceHistory, Stock
from app.services.market_data import fetch_latest_price
from app.services.news import fetch_news_for_symbol

MODEL = "claude-haiku-4-5-20251001"
CACHE_HOURS = 6


async def analyze_stock(
    db: AsyncSession, symbol: str, user_id: uuid.UUID, force: bool = False
) -> dict:
    """Run AI analysis on a stock and return a recommendation.

    Returns a cached recommendation if one exists within CACHE_HOURS,
    unless force=True.
    """
    symbol = symbol.upper()

    # Check for recent cached recommendation
    if not force:
        cached = await _get_cached_recommendation(db, symbol, user_id)
        if cached is not None:
            return cached

    # Gather data
    price_data = await fetch_latest_price(db, symbol)
    news = await fetch_news_for_symbol(db, symbol, limit=5)

    # Get 30-day history from DB
    stock_result = await db.execute(select(Stock).where(Stock.symbol == symbol))
    stock = stock_result.scalar_one_or_none()
    if stock is None:
        raise ValueError(f"Stock {symbol} not found")

    cutoff = datetime.now(timezone.utc).date() - timedelta(days=30)
    history_result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.stock_id == stock.id, PriceHistory.date >= cutoff)
        .order_by(PriceHistory.date)
    )
    history = history_result.scalars().all()

    # Summarize OHLCV instead of sending raw lines (saves ~800 tokens)
    history_summary = _summarize_history(history)

    news_text = "\n".join(
        f"- [{n['published_at'][:10]}] {n['headline']}"
        for n in news[:5]
    )

    prompt = f"""Analyze {symbol} ({stock.name}) for investment.

Price: ${price_data['price']} | Prev close: ${price_data.get('previous_close', 'N/A')} | Change: {price_data.get('change_percent', 'N/A')}%

{history_summary}

News:
{news_text or 'No recent news'}

Respond ONLY with JSON: {{"action":"BUY|SELL|HOLD","confidence":0-100,"summary":"<max 200 chars>","reasoning":"<2-3 paragraphs>"}}"""

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = response.content[0].text.strip()
    # Strip markdown code fences if present
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        lines = lines[1:]  # Remove opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        response_text = "\n".join(lines)

    analysis = json.loads(response_text)

    # Store compact audit snapshot (what data the model saw)
    data_snapshot = {
        "price": price_data.get("price"),
        "previous_close": price_data.get("previous_close"),
        "history_summary": history_summary,
        "news_count": len(news),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }

    rec = Recommendation(
        stock_id=stock.id,
        user_id=user_id,
        action=analysis["action"],
        confidence=Decimal(str(analysis["confidence"])),
        summary=analysis["summary"],
        reasoning=analysis["reasoning"],
        data_snapshot=data_snapshot,
        model_version=MODEL,
    )
    db.add(rec)

    # Create notification
    notification = Notification(
        user_id=user_id,
        type="recommendation",
        title=f"New {analysis['action']} recommendation for {symbol}",
        message=analysis["summary"],
        reference_id=str(rec.id),
    )
    db.add(notification)

    await db.commit()
    await db.refresh(rec, ["stock"])

    return _rec_to_dict(rec, cached=False)


async def _get_cached_recommendation(
    db: AsyncSession, symbol: str, user_id: uuid.UUID
) -> Optional[dict]:
    """Return a recent recommendation if one exists within CACHE_HOURS."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=CACHE_HOURS)
    result = await db.execute(
        select(Recommendation)
        .options(selectinload(Recommendation.stock))
        .join(Stock)
        .where(
            Stock.symbol == symbol,
            Recommendation.user_id == user_id,
            Recommendation.created_at >= cutoff,
        )
        .order_by(Recommendation.created_at.desc())
        .limit(1)
    )
    rec = result.scalar_one_or_none()
    if rec is None:
        return None
    return _rec_to_dict(rec, cached=True)


def _summarize_history(history) -> str:
    """Summarize OHLCV data into a compact string instead of raw lines."""
    if not history:
        return "30-day history: No data available"

    closes = [h.close for h in history]
    volumes = [h.volume for h in history]
    highs = [h.high for h in history]
    lows = [h.low for h in history]

    first_close = closes[0]
    last_close = closes[-1]
    change_pct = ((last_close - first_close) / first_close * 100).quantize(Decimal("0.01")) if first_close else 0
    avg_vol = sum(volumes) // len(volumes) if volumes else 0

    return (
        f"30-day summary ({len(history)} trading days): "
        f"Change {change_pct}% | "
        f"High ${max(highs)} | Low ${min(lows)} | "
        f"Avg volume {avg_vol:,}"
    )


def _rec_to_dict(rec: Recommendation, cached: bool = False) -> dict:
    result = {
        "id": str(rec.id),
        "stock": {
            "id": str(rec.stock.id),
            "symbol": rec.stock.symbol,
            "name": rec.stock.name,
            "exchange": rec.stock.exchange,
            "asset_type": rec.stock.asset_type,
        },
        "action": rec.action,
        "confidence": str(rec.confidence),
        "summary": rec.summary,
        "reasoning": rec.reasoning,
        "model_version": rec.model_version,
        "created_at": rec.created_at.isoformat(),
        "cached": cached,
    }
    return result
