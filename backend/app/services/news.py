from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.news import NewsArticle, NewsArticleStock
from app.models.stock import Stock
from app.services.market_data import _alpaca_headers


async def fetch_news_for_symbol(db: AsyncSession, symbol: str, limit: int = 20) -> list[dict]:
    """Fetch news from Alpaca News API for a given symbol."""
    symbol = symbol.upper()

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
    results = []

    # Get or create stock
    stock_result = await db.execute(select(Stock).where(Stock.symbol == symbol))
    stock = stock_result.scalar_one_or_none()

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
            )
            db.add(news_article)
            await db.flush()

            # Link to stock
            if stock:
                db.add(NewsArticleStock(news_article_id=news_article.id, stock_id=stock.id))

        results.append({
            "id": str(news_article.id),
            "headline": news_article.headline,
            "summary": news_article.summary,
            "url": news_article.url,
            "source": news_article.source,
            "published_at": news_article.published_at.isoformat(),
        })

    await db.commit()
    return results
