import uuid
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.portfolio import Holding, Portfolio
from app.models.user import User
from app.schemas.portfolio import (
    HoldingCreate,
    HoldingUpdate,
    HoldingResponse,
    PortfolioCreate,
    PortfolioListResponse,
    PortfolioResponse,
    PortfolioUpdate,
)
from app.services.auth import get_current_user
from app.services.market_data import get_or_create_stock

router = APIRouter(prefix="/api/portfolios", tags=["portfolios"])


async def _get_user_portfolio(db: AsyncSession, portfolio_id: uuid.UUID, user_id: uuid.UUID) -> Portfolio:
    result = await db.execute(
        select(Portfolio)
        .options(selectinload(Portfolio.holdings).selectinload(Holding.stock))
        .where(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
    )
    portfolio = result.scalar_one_or_none()
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.get("", response_model=list[PortfolioListResponse])
async def list_portfolios(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Portfolio)
        .options(selectinload(Portfolio.holdings))
        .where(Portfolio.user_id == user.id)
        .order_by(Portfolio.created_at.desc())
    )
    portfolios = result.scalars().all()
    return [
        PortfolioListResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            holdings_count=len(p.holdings),
            created_at=p.created_at,
        )
        for p in portfolios
    ]


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    data: PortfolioCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    portfolio = Portfolio(user_id=user.id, name=data.name, description=data.description)
    db.add(portfolio)
    await db.commit()
    await db.refresh(portfolio, ["holdings"])
    return portfolio


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await _get_user_portfolio(db, portfolio_id, user.id)


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: uuid.UUID,
    data: PortfolioUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    portfolio = await _get_user_portfolio(db, portfolio_id, user.id)
    if data.name is not None:
        portfolio.name = data.name
    if data.description is not None:
        portfolio.description = data.description
    await db.commit()
    await db.refresh(portfolio, ["holdings"])
    return portfolio


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    portfolio = await _get_user_portfolio(db, portfolio_id, user.id)
    await db.delete(portfolio)
    await db.commit()


# --- Holdings ---


@router.post("/{portfolio_id}/holdings", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
async def add_holding(
    portfolio_id: uuid.UUID,
    data: HoldingCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    portfolio = await _get_user_portfolio(db, portfolio_id, user.id)

    try:
        quantity = Decimal(data.quantity)
        cost_basis = Decimal(data.avg_cost_basis)
    except InvalidOperation:
        raise HTTPException(status_code=400, detail="Invalid decimal value")

    stock = await get_or_create_stock(db, data.symbol)

    # Check for existing holding
    existing = await db.execute(
        select(Holding).where(Holding.portfolio_id == portfolio.id, Holding.stock_id == stock.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Holding already exists. Use PUT to update.")

    holding = Holding(
        portfolio_id=portfolio.id,
        stock_id=stock.id,
        quantity=quantity,
        avg_cost_basis=cost_basis,
    )
    db.add(holding)
    await db.commit()
    await db.refresh(holding, ["stock"])
    return holding


@router.put("/{portfolio_id}/holdings/{holding_id}", response_model=HoldingResponse)
async def update_holding(
    portfolio_id: uuid.UUID,
    holding_id: uuid.UUID,
    data: HoldingUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_user_portfolio(db, portfolio_id, user.id)

    result = await db.execute(
        select(Holding)
        .options(selectinload(Holding.stock))
        .where(Holding.id == holding_id, Holding.portfolio_id == portfolio_id)
    )
    holding = result.scalar_one_or_none()
    if holding is None:
        raise HTTPException(status_code=404, detail="Holding not found")

    try:
        if data.quantity is not None:
            holding.quantity = Decimal(data.quantity)
        if data.avg_cost_basis is not None:
            holding.avg_cost_basis = Decimal(data.avg_cost_basis)
    except InvalidOperation:
        raise HTTPException(status_code=400, detail="Invalid decimal value")

    await db.commit()
    await db.refresh(holding, ["stock"])
    return holding


@router.delete("/{portfolio_id}/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holding(
    portfolio_id: uuid.UUID,
    holding_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_user_portfolio(db, portfolio_id, user.id)

    result = await db.execute(
        select(Holding).where(Holding.id == holding_id, Holding.portfolio_id == portfolio_id)
    )
    holding = result.scalar_one_or_none()
    if holding is None:
        raise HTTPException(status_code=404, detail="Holding not found")

    await db.delete(holding)
    await db.commit()
