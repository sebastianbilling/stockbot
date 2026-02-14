import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class StockResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    name: str
    exchange: Optional[str]
    asset_type: str

    model_config = {"from_attributes": True}


class LatestPriceResponse(BaseModel):
    symbol: str
    name: str
    price: str
    previous_close: Optional[str]
    change_percent: Optional[str]
    fetched_at: datetime


class PriceHistoryResponse(BaseModel):
    date: date
    open: str
    high: str
    low: str
    close: str
    volume: int
    vwap: Optional[str]


class StockSearchResult(BaseModel):
    symbol: str
    name: str
    exchange: Optional[str]
    asset_type: str
