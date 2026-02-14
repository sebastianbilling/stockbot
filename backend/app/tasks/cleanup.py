from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.stock import PriceHistory
from app.services.news import cleanup_old_news


async def run_cleanup(db: AsyncSession) -> dict:
    """Delete old data to keep DB size small. Returns counts of deleted rows."""
    results = {}

    # 1. Read notifications older than 30 days
    notif_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    notif_result = await db.execute(
        delete(Notification).where(
            Notification.is_read == True,  # noqa: E712
            Notification.created_at < notif_cutoff,
        )
    )
    results["notifications_deleted"] = notif_result.rowcount

    # 2. Price history older than 1 year
    history_cutoff = datetime.now(timezone.utc).date() - timedelta(days=365)
    history_result = await db.execute(
        delete(PriceHistory).where(PriceHistory.date < history_cutoff)
    )
    results["price_history_deleted"] = history_result.rowcount

    # 3. Old news articles (> 7 days)
    news_deleted = await cleanup_old_news(db, days=7, commit=False)
    results["news_articles_deleted"] = news_deleted

    # Single atomic commit for all cleanup operations
    await db.commit()
    return results
