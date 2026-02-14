from datetime import datetime, timedelta, timezone
from typing import List

import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.news import NewsArticle, NewsArticleStock
from app.models.stock import Stock
from app.services.market_data import _alpaca_headers

NEWS_CACHE_HOURS = 2


async def fetch_news_for_symbol(db: AsyncSession, symbol: str, limit: int = 20) -> List[dict]:
    """Fetch news for a symbol. Serves from DB cache if fresh, otherwise fetches from Alpaca."""
    symbol = symbol.upper()

    # Check DB cache: do we have recent articles linked to this stock?
    stock_result = await db.execute(select(Stock).where(Stock.symbol == symbol))
    stock = stock_result.scalar_one_or_none()

    if stock:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=NEWS_CACHE_HOURS)
        cached_result = await db.execute(
            select(NewsArticle)
            .join(NewsArticleStock, NewsArticle.id == NewsArticleStock.news_article_id)
            .where(
                NewsArticleStock.stock_id == stock.id,
                NewsArticle.fetched_at >= cutoff,
            )
            .order_by(NewsArticle.published_at.desc())
            .limit(limit)
        )
        cached = cached_result.scalars().all()
        if cached:
            return [_article_to_dict(a) for a in cached]

    # Cache miss — fetch from Alpaca
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.alpaca_base_url}/v1beta1/news",
            headers=_alpaca_headers(),
            params={"symbols": symbol, "limit": limit, "sort": "desc"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

    articles = data.get("news") or []
    if not articles:
        return []

    # Ensure stock exists
    if stock is None:
        stock = Stock(symbol=symbol, name=symbol)
        db.add(stock)
        await db.flush()

    now = datetime.now(timezone.utc)
    results = []
    for article in articles:
        ext_id = str(article["id"])
        existing = await db.execute(select(NewsArticle).where(NewsArticle.external_id == ext_id))
        news_article = existing.scalar_one_or_none()

        published = datetime.fromisoformat(article["created_at"].replace("Z", "+00:00"))

        if news_article is None:
            news_article = NewsArticle(
                external_id=ext_id,
                headline=article.get("headline", ""),
                summary=article.get("summary"),
                url=article.get("url"),
                source=article.get("source"),
                published_at=published,
                fetched_at=now,
            )
            db.add(news_article)
            await db.flush()

            db.add(NewsArticleStock(news_article_id=news_article.id, stock_id=stock.id))
        else:
            # Update fetch timestamp so cache TTL resets
            news_article.fetched_at = now

        results.append(_article_to_dict(news_article))

    await db.commit()
    return results


async def cleanup_old_news(db: AsyncSession, days: int = 7, commit: bool = True) -> int:
    """Delete news articles older than `days`. Returns count deleted."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    # Delete join table rows first (cascade should handle this, but be explicit)
    old_ids_query = select(NewsArticle.id).where(NewsArticle.published_at < cutoff)
    await db.execute(
        delete(NewsArticleStock).where(NewsArticleStock.news_article_id.in_(old_ids_query))
    )
    result = await db.execute(delete(NewsArticle).where(NewsArticle.published_at < cutoff))
    if commit:
        await db.commit()
    return result.rowcount


def _article_to_dict(a: NewsArticle) -> dict:
    return {
        "id": str(a.id),
        "headline": a.headline,
        "summary": a.summary,
        "url": a.url,
        "source": a.source,
        "published_at": a.published_at.isoformat(),
    }
