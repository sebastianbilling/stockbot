import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None


class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class HoldingCreate(BaseModel):
    symbol: str
    quantity: str  # Decimal as string
    avg_cost_basis: str  # Decimal as string


class HoldingUpdate(BaseModel):
    quantity: Optional[str] = None
    avg_cost_basis: Optional[str] = None


class StockInHolding(BaseModel):
    id: uuid.UUID
    symbol: str
    name: str

    model_config = {"from_attributes": True}


class HoldingResponse(BaseModel):
    id: uuid.UUID
    stock: StockInHolding
    quantity: str
    avg_cost_basis: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PortfolioResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    holdings: List[HoldingResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PortfolioListResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    holdings_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
