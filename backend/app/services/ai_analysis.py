import json
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.notification import Notification
from app.models.recommendation import Recommendation
from app.models.stock import PriceHistory, Stock
from app.services.market_data import fetch_latest_price
from app.services.news import fetch_news_for_symbol

MODEL = "claude-haiku-4-5-20251001"


async def analyze_stock(db: AsyncSession, symbol: str, user_id: uuid.UUID) -> dict:
    """Run AI analysis on a stock and return a recommendation."""
    symbol = symbol.upper()

    # Gather data
    price_data = await fetch_latest_price(db, symbol)
    news = await fetch_news_for_symbol(db, symbol, limit=10)

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

    history_text = "\n".join(
        f"  {h.date}: O={h.open} H={h.high} L={h.low} C={h.close} V={h.volume}"
        for h in history
    )

    news_text = "\n".join(
        f"  [{n['published_at'][:10]}] {n['headline']}"
        for n in news[:10]
    )

    prompt = f"""Analyze the stock {symbol} ({stock.name}) and provide an investment recommendation.

Current price: ${price_data['price']}
Previous close: ${price_data.get('previous_close', 'N/A')}
Change: {price_data.get('change_percent', 'N/A')}%

30-day OHLCV history:
{history_text or '  No history available'}

Recent news:
{news_text or '  No recent news'}

Provide your analysis as JSON with these exact fields:
- "action": one of "BUY", "SELL", or "HOLD"
- "confidence": a number from 0 to 100
- "summary": a one-sentence summary (max 200 chars)
- "reasoning": detailed reasoning (2-4 paragraphs)

IMPORTANT: This is for advisory purposes only. Respond ONLY with valid JSON, no markdown."""

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
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

    # Store snapshot for auditability
    data_snapshot = {
        "price": price_data,
        "history_count": len(history),
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

    return {
        "id": str(rec.id),
        "stock": {
            "id": str(stock.id),
            "symbol": stock.symbol,
            "name": stock.name,
            "exchange": stock.exchange,
            "asset_type": stock.asset_type,
        },
        "action": rec.action,
        "confidence": str(rec.confidence),
        "summary": rec.summary,
        "reasoning": rec.reasoning,
        "model_version": rec.model_version,
        "created_at": rec.created_at.isoformat(),
    }
