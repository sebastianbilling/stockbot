# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stockbot is an **AI-powered investment advisory platform** — a full-stack web app where users manage stock portfolios, view live market data, and get AI-generated buy/sell/hold recommendations via Claude.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.9, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL |
| Frontend | Next.js 16, React 19, TailwindCSS, shadcn/ui, React Query |
| Auth | JWT (python-jose) → NextAuth v5 credentials provider |
| Market Data | Alpaca Markets API (IEX free feed) |
| AI Analysis | Anthropic Claude Haiku 4.5 |
| Package Mgmt | `uv` (backend), `npm` (frontend) |

## Running Locally

```bash
docker-compose up -d                          # PostgreSQL on :5432
cd backend && alembic upgrade head            # Run migrations
cd backend && python -m uvicorn app.main:app --reload  # API on :8000
cd frontend && npm run dev                    # UI on :3000
```

Requires `backend/.env` with `ALPACA_API_KEY`, `ALPACA_API_SECRET`, `ANTHROPIC_API_KEY`.

## Architecture

```
backend/app/
  api/           # FastAPI routers (auth, portfolios, stocks, recommendations, notifications)
  models/        # SQLAlchemy models (User, Portfolio, Holding, Stock, PriceHistory, etc.)
  schemas/       # Pydantic request/response schemas
  services/      # Business logic (auth, market_data, news, ai_analysis)
  tasks/         # Startup cleanup (data retention)

frontend/src/
  app/(app)/     # Authenticated pages (dashboard, portfolios, stocks, recommendations)
  components/    # shadcn/ui components + stock search
  lib/           # API client, decimal helpers, auth hooks
  types/         # TypeScript interfaces
```

## Key Domain Principles

- **Never use floating-point for financial calculations** — `NUMERIC(19,4)` in DB, `Decimal` in Python, strings in JSON, `decimal.js` in frontend
- **Audit trails** on all state-changing operations — recommendations store `data_snapshot` of inputs
- **Correctness over performance** — deterministic, auditable behavior is paramount
- **Input validation** — stock symbols validated with regex `[A-Z]{1,10}`, batch endpoints capped at 50

## Cost Optimization (MVP Constraints)

This app is designed to minimize API and hosting costs:

- **Alpaca API**: Asset list cached in-memory 24h with asyncio.Lock; prices cached 30min in DB; price history served from DB first; batch snapshot endpoint for portfolio pages (1 call instead of N)
- **Anthropic API**: 6h recommendation cache per stock/user; OHLCV summarized (not raw) in prompts; max_tokens=512; rate limited to 10 analyses/hour/user
- **DB storage**: News cached 2h then pruned after 7 days; price history pruned after 1 year; read notifications pruned after 30 days; cleanup runs on app startup
- **No background jobs** — user refreshes manually; no WebSocket/polling
- **Target hosting**: Vercel free (frontend) + Render/Fly.io free (backend) + Neon free (Postgres)

## Agent Architecture

Four specialized agents in `.claude/agents/`:

| Agent | Role |
|-------|------|
| **fintech-tpm** | Project management, sprint planning, regulatory compliance |
| **hft-backend-architect** | Backend architecture, caching, data flow, security reviews |
| **realtime-finance-ui-lead** | Frontend architecture, React Query, data visualization |
| **security-vulnerability-scanner** | Vulnerability detection, OWASP/CWE analysis |

All agents use Opus and maintain memory in `.claude/agent-memory/<agent-name>/`.

## Python Constraints

- System Python is 3.9.6 — use `Optional[X]` from typing, not `X | None`
- passlib + bcrypt 5.x incompatible — bcrypt pinned to 4.2.1
- Alembic uses `psycopg2` (sync), app uses `asyncpg` (async)
