import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.recommendation import Recommendation
from app.models.user import User
from app.services.ai_analysis import analyze_stock
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("")
async def list_recommendations(
    action: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Recommendation)
        .options(selectinload(Recommendation.stock))
        .where(Recommendation.user_id == user.id)
        .order_by(Recommendation.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if action:
        query = query.where(Recommendation.action == action.upper())

    result = await db.execute(query)
    recs = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "stock": {
                "id": str(r.stock.id),
                "symbol": r.stock.symbol,
                "name": r.stock.name,
                "exchange": r.stock.exchange,
                "asset_type": r.stock.asset_type,
            },
            "action": r.action,
            "confidence": str(r.confidence),
            "summary": r.summary,
            "created_at": r.created_at.isoformat(),
        }
        for r in recs
    ]


@router.get("/{rec_id}")
async def get_recommendation(
    rec_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Recommendation)
        .options(selectinload(Recommendation.stock))
        .where(Recommendation.id == rec_id, Recommendation.user_id == user.id)
    )
    rec = result.scalar_one_or_none()
    if rec is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    return {
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
    }


@router.post("/analyze/{symbol}")
async def trigger_analysis(
    symbol: str,
    force: bool = Query(False, description="Bypass 6h cache and force fresh analysis"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Rate limit: always enforced (counts actual analyses created in the last hour)
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    count_result = await db.execute(
        select(func.count())
        .select_from(Recommendation)
        .where(Recommendation.user_id == user.id, Recommendation.created_at >= one_hour_ago)
    )
    count = count_result.scalar()
    if count >= 10:
        raise HTTPException(status_code=429, detail="Rate limit: max 10 analyses per hour")

    return await analyze_stock(db, symbol, user.id, force=force)
