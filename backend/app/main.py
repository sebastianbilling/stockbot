from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, notifications, portfolios, recommendations, stocks
from app.tasks.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Stockbot API",
    description="AI-Powered Investment Advisor",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(portfolios.router)
app.include_router(stocks.router)
app.include_router(recommendations.router)
app.include_router(notifications.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
