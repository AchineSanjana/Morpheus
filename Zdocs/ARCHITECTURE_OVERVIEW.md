# 🏗️ Morpheus Sleep AI – System Architecture Overview

Version: 1.0
Last Updated: October 17, 2025
Owner: Engineering
Classification: Internal

---

Note: This is the canonical high-level architecture overview for Morpheus. For a deeper, implementation-focused view (tiers, scaling, and sample flows), see `SYSTEM_ARCHITECTURE.md`.

## 📋 Table of Contents

1. Executive Summary
2. High-level Architecture
3. Component Architecture
4. Data Architecture (Supabase)
5. Request Lifecycle
6. Security Architecture (at a glance)
7. Responsible AI Integration
8. Deployment Architecture
9. Configuration & Environments
10. Observability & Ops
11. Future Enhancements

---

## 1) 🎯 Executive Summary

Morpheus is a full‑stack, multi-agent AI application for sleep improvement. It uses a React (Vite) frontend, a FastAPI backend with modular agents, and Supabase for authentication, database, and storage. Security and Responsible AI are first-class citizens.

Core patterns:
- Multi-tier architecture (Client → API → Agents → AI/DB)
- Multi-agent orchestration via a Coordinator agent
- Defense-in-depth security layers
- Responsible AI checks on every response
- Supabase-managed auth, data, storage with RLS

---

## 2) 🗺️ High-level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                               Client (Web)                           │
│  React + Vite + Tailwind                                             │
│  • Chat UI  • Account/Profile  • Responsible AI panels               │
└───────────────▲──────────────────────────────────────────────────────┘
                │ HTTPS (JWT via Supabase)
┌───────────────┴──────────────────────────────────────────────────────┐
│                           FastAPI Backend                             │
│  main.py                                                              │
│  • CORS/Headers  • Rate limiting  • Security validation               │
│  • Routes: /chat/stream, /profile, /sleep-log                         │
│             │                                      │                  │
│             │                                      │                  │
│     Responsible AI (responsible_ai.py)     Security Middleware        │
│     • Safety/Fairness/Privacy checks       (security_middleware.py)   │
│     • Transparency metadata                • Headers / IP / limits     │
│             │                                      │                  │
│             ▼                                      ▼                  │
│                     Coordinator Agent (agents/coordinator.py)         │
│                     • Routes request to specialist agents             │
│   ┌────────────────────┬───────────────────┬───────────────────────┐  │
│   │ Storyteller        │ Coach             │ Analyst / Information │  │
│   │ (agents/storyteller│ (agents/coach.py) │ (agents/analyst.py,   │  │
│   │ .py)               │                   │ information.py)       │  │
│   └────────────────────┴───────────────────┴───────────────────────┘  │
│                                   │                                   │
│                                   ▼                                   │
│                             LLM Gateway                               │
│                           (llm_gemini.py)                              │
└───────────────────────────────┬────────────────────────────────────────┘
                                │
                                ▼
                     Supabase (Auth / Postgres / Storage)
                     • JWT auth • RLS • Profiles • Sleep logs
```

---

## 3) 🧩 Component Architecture

Frontend (React, Vite, Tailwind)
- `src/components/Chat.tsx` – streaming chat UI, shows Responsible AI analysis
- `src/components/Account.tsx` – profile view/edit, avatar upload
- `src/components/ResponsibleAI.tsx` – transparency, data controls, fairness info
- `src/components/PrivacyPolicy.tsx` – privacy policy content used in in-app modals
- `src/lib/api.ts` – API client and streaming helpers
- `src/lib/supabaseClient.ts` – two clients exported: `supabase` (persists to localStorage) and `supabaseSession` (sessionStorage) to support the “Remember me” choice

Backend (FastAPI, Python)
- `app/main.py` – app init, routes, CORS, security headers, dependency wiring
- `app/db.py` – Supabase integration (auth verify, CRUD helpers)
- `app/llm_gemini.py` – LLM wrapper/gateway for Gemini calls
- `app/responsible_ai.py` – safety, transparency, fairness, privacy checks
- `app/security_middleware.py` – rate limiting, request validation, headers
- `app/security_config.py` – env-based security config, encryption helpers
- `app/agents/` – multi-agent layer
  - `coordinator.py` – routes intent to agents, merges results
  - `storyteller.py` – secure bedtime story generation with fallback content
  - `coach.py`, `analyst.py`, `information.py`, `nutrition.py`, `addiction.py` – specialist logic

---

## 4) 🗄️ Data Architecture (Supabase)

Primary data store: Supabase (PostgreSQL) with Row-Level Security (RLS)

Suggested/typical tables:
- `profiles` (or `user_profile`) – id (auth.users.id), full_name, username, avatar_url, timestamps
- `sleep_logs` – user_id, date, duration, quality, notes
- `chat_messages` – id, user_id, role (user/ai), content, metadata, created_at
- `user_preferences` – user_id, jsonb preferences (themes, story tone, etc.)

Storage:
- Bucket for `avatars` (publicly served via signed URLs)

Auth:
- Supabase Auth with JWT; RLS policies restrict data to `auth.uid()`

---

## 5) 🔄 Request Lifecycle

Example: Chat streaming

1) Frontend sends POST `/chat/stream` with JWT in `Authorization: Bearer <token>`
2) Backend middleware applies:
   - CORS and security headers
   - Rate limiting and request validation
3) `get_current_user()` verifies token against Supabase Auth
4) SecurityValidator sanitizes input; ResponsibleAI pre-checks risk
5) Coordinator routes to the appropriate agent (e.g., Storyteller)
6) Agent may call `llm_gemini.py` or use safe fallbacks
7) ResponsibleAI post-check validates content; metadata attached
8) StreamingResponse returns chunks to frontend
9) Optional: persist message to `chat_messages` with minimal PII

Profile flow
- GET `/profile/{user_id}`: fetch or create profile (id from JWT)
- POST `/profile/{user_id}`: update limited editable fields with RLS

---

## 6) 🛡️ Security Architecture (at a glance)

Layers
- Edge: TLS, strict security headers, tight CORS
- API: rate limiting (IP or token-based), request validation, input size caps
- Application: input sanitization, output validation, safe fallbacks
- Data: RLS policies, least-privilege, encrypted secrets
- Monitoring: structured security events, anomaly thresholds

Key controls
- Prompt injection filtering and XSS/SQL pattern sanitization
- Content validation for age-appropriateness, PII, medical disclaimers
- Audit-friendly logging using content hashes (no raw sensitive text)

(See `Zdocs/SECURITY_DOCUMENTATION.md` for full detail.)

---

## 7) 🤖 Responsible AI Integration

Pipeline checkpoints
- Pre-generation: risk/safety assessment (toxicity, bias, PII)
- Generation constraints: safe prompts, temperature/tokens bounds
- Post-generation: safety re-check, fairness/bias scan, transparency metadata
- UX: Responsible AI panels explain how and why responses were generated

Outputs include
- Rationale, safety scores, filtered content reasons, data usage notes

---

## 8) 🚀 Deployment Architecture

Common production layout

- Frontend: Static hosting (e.g., Netlify or any static CDN)
- Backend: Railway/Render/Fly.io (FastAPI + Uvicorn/Gunicorn)
- Database/Auth/Storage: Supabase (managed Postgres + Auth + Storage)
- Optional: Redis for distributed rate limiting and caching

Network
- HTTPS only; backend exposes `/chat/stream`, `/profile`, `/sleep-log`
- CORS origins restricted to your frontend domain(s)

Scaling
- Stateless backend instances behind a load balancer
- DB connection pooling (Supabase handles pool); use async clients
- Horizontal scale of backend and CDN caching for frontend

---

## 9) ⚙️ Configuration & Environments

Key environment variables (backend)
- `ENVIRONMENT` = production | development
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE`
- `GEMINI_API_KEY`
- `CORS_ORIGINS` = comma-separated allowed origins
- `API_RATE_LIMIT_ENABLED`, `CONTENT_VALIDATION_ENABLED`, `PROMPT_INJECTION_PROTECTION`
- `ENCRYPTION_KEY` (32-byte for Fernet if used)

Frontend (Vite)
- `VITE_API_URL` = https://your-backend
- `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`

---

## 10) 📈 Observability & Ops

- Structured logs for security events and application metrics
- Useful KPIs: rate-limit hits, auth failures, safety-block counts, latency
- Error tracking: integrate with Sentry/Elastic (optional)
- Health endpoints (optional) for readiness/liveness

Runbooks
- Incident response and thresholds are documented in `Zdocs/SECURITY_DOCUMENTATION.md`

---

## 11) 🔭 Future Enhancements

- Redis-backed, per-user rate limiting for distributed environments
- Feature flags for progressive rollout of agents and prompts
- Background jobs (RQ/Celery) for analytics aggregation
- Real-time features via Supabase Realtime for live updates
- Expanded test coverage for agents and safety checks

---

## 📎 File ↔ Responsibility Map (Quick Reference)

- Frontend
  - `frontend/src/components/Chat.tsx` – chat UI, streaming, safety panel
  - `frontend/src/components/Account.tsx` – profile UI + avatar
  - `frontend/src/components/ResponsibleAI.tsx` – responsible AI UI widgets
  - `frontend/src/lib/api.ts` – API wrappers
  - `frontend/src/lib/supabaseClient.ts` – auth client

- Backend
  - `backend/app/main.py` – app wiring, routes, CORS, middleware
  - `backend/app/db.py` – Supabase auth + persistence helpers
  - `backend/app/llm_gemini.py` – Gemini API gateway
  - `backend/app/responsible_ai.py` – safety/fairness/transparency checks
  - `backend/app/security_middleware.py` – rate limiting, validation, headers
  - `backend/app/security_config.py` – security config and helpers
  - `backend/app/agents/*` – coordinator + specialist agents

- Database
  - `database/*` – migrations/policies/bucket setup (as applicable)

---

This document provides a practical blueprint for developing, operating, and scaling Morpheus while preserving security and responsible AI principles. For deep security details, see `Zdocs/SECURITY_DOCUMENTATION.md`.
