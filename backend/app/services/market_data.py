import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.stock import LatestPrice, PriceHistory, Stock

CACHE_MINUTES = 30

# In-memory cache for Alpaca asset list (rarely changes)
_asset_cache: Optional[List[Dict]] = None
_asset_cache_time: Optional[datetime] = None
_asset_lock = asyncio.Lock()
_ASSET_CACHE_HOURS = 24


def _alpaca_headers() -> Dict[str, str]:
    return {
        "APCA-API-KEY-ID": settings.alpaca_api_key,
        "APCA-API-SECRET-KEY": settings.alpaca_api_secret,
    }


async def _get_cached_assets() -> List[Dict]:
    """Return the full Alpaca asset list, cached in memory for 24h."""
    global _asset_cache, _asset_cache_time

    now = datetime.now(timezone.utc)
    if (
        _asset_cache is not None
        and _asset_cache_time is not None
        and (now - _asset_cache_time) < timedelta(hours=_ASSET_CACHE_HOURS)
    ):
        return _asset_cache

    async with _asset_lock:
        # Double-check after acquiring lock (another request may have refreshed)
        if (
            _asset_cache is not None
            and _asset_cache_time is not None
            and (datetime.now(timezone.utc) - _asset_cache_time) < timedelta(hours=_ASSET_CACHE_HOURS)
        ):
            return _asset_cache

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://paper-api.alpaca.markets/v2/assets",
                headers=_alpaca_headers(),
                params={"status": "active", "asset_class": "us_equity"},
                timeout=15,
            )
            resp.raise_for_status()
            assets = resp.json()

        # Only keep tradable assets and store minimal fields
        _asset_cache = [
            {
                "symbol": a["symbol"],
                "name": a.get("name", ""),
                "exchange": a.get("exchange"),
                "asset_type": "stock",
            }
            for a in assets
            if a.get("tradable")
        ]
        _asset_cache_time = datetime.now(timezone.utc)
        return _asset_cache


async def search_stocks(query: str) -> List[Dict]:
    """Search for stocks from cached asset list."""
    assets = await _get_cached_assets()
    query_upper = query.upper()
    query_lower = query.lower()

    results = []
    for asset in assets:
        if query_upper in asset["symbol"] or query_lower in asset["name"].lower():
            results.append(asset)
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


async def _load_stock_with_price(db: AsyncSession, symbol: str) -> Stock:
    """Load a stock with its latest_price eagerly loaded."""
    result = await db.execute(
        select(Stock)
        .options(selectinload(Stock.latest_price))
        .where(Stock.symbol == symbol)
    )
    stock = result.scalar_one_or_none()
    if stock is None:
        stock = Stock(symbol=symbol, name=symbol)
        db.add(stock)
        await db.flush()
        # Re-load with relationship
        result = await db.execute(
            select(Stock)
            .options(selectinload(Stock.latest_price))
            .where(Stock.id == stock.id)
        )
        stock = result.scalar_one()
    return stock


async def fetch_latest_price(db: AsyncSession, symbol: str) -> Dict:
    """Fetch latest price from Alpaca, with 30min DB cache."""
    symbol = symbol.upper()
    stock = await _load_stock_with_price(db, symbol)

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
            params={"feed": "iex"},
            timeout=10,
        )
        if resp.status_code == 403:
            raise HTTPException(status_code=502, detail="Alpaca API access denied. Check your API plan and keys.")
        resp.raise_for_status()
        data = resp.json()

    _upsert_price_from_snapshot(stock, data)
    await db.commit()
    await db.refresh(stock, ["latest_price"])
    return _price_to_dict(stock, stock.latest_price)


async def fetch_batch_prices(db: AsyncSession, symbols: List[str]) -> Dict[str, Dict]:
    """Fetch prices for multiple symbols in one Alpaca call. Uses DB cache where fresh."""
    symbols = [s.upper() for s in symbols]
    results: Dict[str, Dict] = {}
    stale_symbols: List[str] = []
    stock_map: Dict[str, Stock] = {}

    # Check cache for each symbol
    for symbol in symbols:
        stock = await _load_stock_with_price(db, symbol)
        stock_map[symbol] = stock
        if stock.latest_price:
            age = datetime.now(timezone.utc) - stock.latest_price.fetched_at
            if age < timedelta(minutes=CACHE_MINUTES):
                results[symbol] = _price_to_dict(stock, stock.latest_price)
                continue
        stale_symbols.append(symbol)

    if not stale_symbols:
        return results

    # Batch fetch stale symbols from Alpaca (1 API call for all)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.alpaca_base_url}/v2/stocks/snapshots",
            headers=_alpaca_headers(),
            params={"symbols": ",".join(stale_symbols), "feed": "iex"},
            timeout=15,
        )
        if resp.status_code == 403:
            raise HTTPException(status_code=502, detail="Alpaca API access denied. Check your API plan and keys.")
        resp.raise_for_status()
        snapshots = resp.json()

    for symbol in stale_symbols:
        data = snapshots.get(symbol)
        if data is None:
            continue
        stock = stock_map[symbol]
        _upsert_price_from_snapshot(stock, data)
        await db.flush()
        await db.refresh(stock, ["latest_price"])
        results[symbol] = _price_to_dict(stock, stock.latest_price)

    await db.commit()
    return results


def _upsert_price_from_snapshot(stock: Stock, data: Dict) -> None:
    """Update or create a LatestPrice from an Alpaca snapshot response."""
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
        stock.latest_price = lp


async def fetch_price_history(db: AsyncSession, symbol: str, period: str = "1M") -> List[Dict]:
    """Fetch OHLCV price history. Serves from DB if data exists for the range, otherwise fetches from Alpaca."""
    symbol = symbol.upper()
    stock = await get_or_create_stock(db, symbol)

    period_map = {"1W": 7, "1M": 30, "3M": 90, "6M": 180, "1Y": 365}
    days = period_map.get(period, 30)

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    start_date = start.date()
    end_date = end.date()

    # Check DB for existing bars in the date range
    db_result = await db.execute(
        select(PriceHistory)
        .where(
            PriceHistory.stock_id == stock.id,
            PriceHistory.date >= start_date,
            PriceHistory.date <= end_date,
        )
        .order_by(PriceHistory.date)
    )
    existing_bars = db_result.scalars().all()

    # If we have a reasonable number of bars AND the most recent is fresh, serve from DB
    # (trading days ~= 5/7 of calendar days, give some tolerance)
    expected_trading_days = max(1, int(days * 5 / 7) - 2)
    if len(existing_bars) >= expected_trading_days:
        most_recent = existing_bars[-1].date  # bars ordered by date asc
        days_since_latest = (end_date - most_recent).days
        # Allow 3 days gap for weekends/holidays
        if days_since_latest <= 3:
            return [_bar_to_dict(bar) for bar in existing_bars]

    # Fetch from Alpaca
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.alpaca_base_url}/v2/stocks/{symbol}/bars",
            headers=_alpaca_headers(),
            params={
                "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "timeframe": "1Day",
                "limit": days,
                "feed": "iex",
            },
            timeout=10,
        )
        if resp.status_code == 403:
            raise HTTPException(status_code=502, detail="Alpaca API access denied. Check your API plan and keys.")
        resp.raise_for_status()
        data = resp.json()

    bars = data.get("bars") or []
    existing_dates = {bar.date for bar in existing_bars}
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

        # Only insert bars we don't already have
        if bar_date not in existing_dates:
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


def _bar_to_dict(bar: PriceHistory) -> Dict:
    return {
        "date": bar.date.isoformat(),
        "open": str(bar.open),
        "high": str(bar.high),
        "low": str(bar.low),
        "close": str(bar.close),
        "volume": bar.volume,
        "vwap": str(bar.vwap) if bar.vwap else None,
    }


def _price_to_dict(stock: Stock, lp: LatestPrice) -> Dict:
    return {
        "symbol": stock.symbol,
        "name": stock.name,
        "price": str(lp.price),
        "previous_close": str(lp.previous_close) if lp.previous_close else None,
        "change_percent": str(lp.change_percent) if lp.change_percent else None,
        "fetched_at": lp.fetched_at.isoformat(),
    }
