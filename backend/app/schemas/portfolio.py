import uuid
from datetime import datetime
from typing import List, Optional

from decimal import Decimal

from pydantic import BaseModel, field_serializer


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
    quantity: Decimal
    avg_cost_basis: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("quantity", "avg_cost_basis")
    def serialize_decimal(self, v: Decimal) -> str:
        return str(v)


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
