import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.stock import StockResponse


class RecommendationResponse(BaseModel):
    id: uuid.UUID
    stock: StockResponse
    action: str
    confidence: str
    summary: str
    reasoning: str
    model_version: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class RecommendationListResponse(BaseModel):
    id: uuid.UUID
    stock: StockResponse
    action: str
    confidence: str
    summary: str
    created_at: datetime

    model_config = {"from_attributes": True}
