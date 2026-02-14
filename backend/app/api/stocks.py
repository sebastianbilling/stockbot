from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth import get_current_user
from app.services.market_data import fetch_latest_price, fetch_price_history, search_stocks
from app.services.news import fetch_news_for_symbol

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/search")
async def search(q: str = Query(..., min_length=1), _=Depends(get_current_user)):
    return await search_stocks(q)


@router.get("/{symbol}/price")
async def get_price(symbol: str, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await fetch_latest_price(db, symbol)


@router.get("/{symbol}/history")
async def get_history(
    symbol: str,
    period: str = Query("1M", pattern="^(1W|1M|3M|6M|1Y)$"),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await fetch_price_history(db, symbol, period)


@router.get("/{symbol}/news")
async def get_news(symbol: str, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await fetch_news_for_symbol(db, symbol)
