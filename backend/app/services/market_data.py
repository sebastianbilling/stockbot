from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.stock import LatestPrice, PriceHistory, Stock

CACHE_MINUTES = 5


def _alpaca_headers() -> Dict[str, str]:
    return {
        "APCA-API-KEY-ID": settings.alpaca_api_key,
        "APCA-API-SECRET-KEY": settings.alpaca_api_secret,
    }


async def search_stocks(query: str) -> List[Dict]:
    """Search for stocks via Alpaca assets endpoint."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://paper-api.alpaca.markets/v2/assets",
            headers=_alpaca_headers(),
            params={"status": "active", "asset_class": "us_equity"},
            timeout=10,
        )
        resp.raise_for_status()
        assets = resp.json()

    query_upper = query.upper()
    results = []
    for asset in assets:
        if asset.get("tradable") and (
            query_upper in asset["symbol"] or query.lower() in asset.get("name", "").lower()
        ):
            results.append({
                "symbol": asset["symbol"],
                "name": asset.get("name", ""),
                "exchange": asset.get("exchange"),
                "asset_type": "stock",
            })
        if len(results) >= 20:
            break
    return results


async def get_or_create_stock(
    db: AsyncSession, symbol: str, name: str = "", exchange: Optional[str] = None
) -> Stock:
    """Get existing stock or create new one."""
    result = await db.execute(select(Stock).where(Stock.symbol == symbol.upper()))
    stock = result.scalar_one_or_none()
    if stock is None:
        stock = Stock(symbol=symbol.upper(), name=name or symbol.upper(), exchange=exchange)
        db.add(stock)
        await db.flush()
    return stock


async def fetch_latest_price(db: AsyncSession, symbol: str) -> Dict:
    """Fetch latest price from Alpaca, with caching."""
    symbol = symbol.upper()
    stock = await get_or_create_stock(db, symbol)

    # Check cache
    if stock.latest_price:
        age = datetime.now(timezone.utc) - stock.latest_price.fetched_at
        if age < timedelta(minutes=CACHE_MINUTES):
            return _price_to_dict(stock, stock.latest_price)

    # Fetch from Alpaca
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.alpaca_base_url}/v2/stocks/{symbol}/snapshot",
            headers=_alpaca_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

    latest_trade_price = Decimal(str(data["latestTrade"]["p"]))
    prev_close = Decimal(str(data["prevDailyBar"]["c"])) if data.get("prevDailyBar") else None
    change_pct = None
    if prev_close and prev_close != 0:
        change_pct = ((latest_trade_price - prev_close) / prev_close * 100).quantize(Decimal("0.0001"))

    now = datetime.now(timezone.utc)
    if stock.latest_price:
        stock.latest_price.price = latest_trade_price
        stock.latest_price.previous_close = prev_close
        stock.latest_price.change_percent = change_pct
        stock.latest_price.fetched_at = now
    else:
        lp = LatestPrice(
            stock_id=stock.id,
            price=latest_trade_price,
            previous_close=prev_close,
            change_percent=change_pct,
            fetched_at=now,
        )
        db.add(lp)

    await db.commit()
    await db.refresh(stock, ["latest_price"])
    return _price_to_dict(stock, stock.latest_price)


async def fetch_price_history(db: AsyncSession, symbol: str, period: str = "1M") -> List[Dict]:
    """Fetch OHLCV price history from Alpaca."""
    symbol = symbol.upper()
    stock = await get_or_create_stock(db, symbol)

    period_map = {"1W": 7, "1M": 30, "3M": 90, "6M": 180, "1Y": 365}
    days = period_map.get(period, 30)

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.alpaca_base_url}/v2/stocks/{symbol}/bars",
            headers=_alpaca_headers(),
            params={
                "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "timeframe": "1Day",
                "limit": days,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

    bars = data.get("bars") or []
    results = []
    for bar in bars:
        bar_date = datetime.fromisoformat(bar["t"].replace("Z", "+00:00")).date()
        results.append({
            "date": bar_date.isoformat(),
            "open": str(Decimal(str(bar["o"]))),
            "high": str(Decimal(str(bar["h"]))),
            "low": str(Decimal(str(bar["l"]))),
            "close": str(Decimal(str(bar["c"]))),
            "volume": bar["v"],
            "vwap": str(Decimal(str(bar["vw"]))) if bar.get("vw") else None,
        })

        # Upsert into price_history
        existing = await db.execute(
            select(PriceHistory).where(
                PriceHistory.stock_id == stock.id, PriceHistory.date == bar_date
            )
        )
        ph = existing.scalar_one_or_none()
        if ph is None:
            db.add(PriceHistory(
                stock_id=stock.id,
                date=bar_date,
                open=Decimal(str(bar["o"])),
                high=Decimal(str(bar["h"])),
                low=Decimal(str(bar["l"])),
                close=Decimal(str(bar["c"])),
                volume=bar["v"],
                vwap=Decimal(str(bar["vw"])) if bar.get("vw") else None,
            ))

    await db.commit()
    return results


def _price_to_dict(stock: Stock, lp: LatestPrice) -> Dict:
    return {
        "symbol": stock.symbol,
        "name": stock.name,
        "price": str(lp.price),
        "previous_close": str(lp.previous_close) if lp.previous_close else None,
        "change_percent": str(lp.change_percent) if lp.change_percent else None,
        "fetched_at": lp.fetched_at.isoformat(),
    }
