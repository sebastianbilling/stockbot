# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **fintech trading platform (stockbot)** workspace with a multi-agent AI coordination system. The project currently consists of agent configurations for specialized domain experts who collaborate on building and maintaining a high-frequency trading platform.

## Agent Architecture

Four specialized agents are defined in `.claude/agents/`:

| Agent | Role | Color |
|-------|------|-------|
| **fintech-tpm** | Technical project management, sprint planning, regulatory compliance | Purple |
| **hft-backend-architect** | Backend system design, low-latency architecture, security reviews | Green |
| **realtime-finance-ui-lead** | Frontend architecture, real-time data visualization, WebSocket streaming | Blue |
| **security-vulnerability-scanner** | Security reviews, vulnerability detection, OWASP/CWE analysis | Red |

All agents use the Opus model. Each agent maintains persistent memory in `.claude/agent-memory/<agent-name>/`.

## Key Domain Principles

- **Never use floating-point for financial calculations** — use fixed-point/decimal arithmetic
- **Correctness over performance** — deterministic, auditable behavior is paramount
- **Defense-in-depth** — mTLS, input validation, rate limiting, audit logging
- **Regulatory compliance** — MiFID II, SEC Reg NMS, Dodd-Frank, SOX, GDPR
- **Audit trails** on all state-changing operations with tamper-evident logging
- **Kill switches and fail-safes** are mandatory for trading systems
