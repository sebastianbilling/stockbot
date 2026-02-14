import uuid
from datetime import datetime

from pydantic import BaseModel


class NewsArticleResponse(BaseModel):
    id: uuid.UUID
    headline: str
    summary: str | None
    url: str | None
    source: str | None
    published_at: datetime

    model_config = {"from_attributes": True}
