import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth import get_current_user
from app.services.market_data import fetch_batch_prices, fetch_latest_price, fetch_price_history, search_stocks
from app.services.news import fetch_news_for_symbol

router = APIRouter(prefix="/api/stocks", tags=["stocks"])

_SYMBOL_RE = re.compile(r"^[A-Z]{1,10}$")
_MAX_BATCH = 50


def _validate_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if not _SYMBOL_RE.match(s):
        raise HTTPException(status_code=400, detail=f"Invalid stock symbol: {symbol}")
    return s


@router.get("/search")
async def search(q: str = Query(..., min_length=1), _=Depends(get_current_user)):
    return await search_stocks(q)


@router.get("/prices")
async def get_batch_prices(
    symbols: str = Query(..., description="Comma-separated stock symbols"),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Fetch prices for multiple symbols in one call (max 50)."""
    symbol_list = [_validate_symbol(s) for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        return {}
    if len(symbol_list) > _MAX_BATCH:
        raise HTTPException(status_code=400, detail=f"Maximum {_MAX_BATCH} symbols per request")
    return await fetch_batch_prices(db, symbol_list)


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
