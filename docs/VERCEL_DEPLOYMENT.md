# Deploying WealthGuard GAA to Vercel (Frontend + Backend)

This guide walks you through deploying the entire **WealthGuard Grounded Advisory Assistant (GAA)** application (Next.js 14 Frontend + FastAPI Python Backend) to **Vercel** in a single atomic deployment.

---

## Architecture Overview

The repository is configured as a **Vercel Services Monorepo** via root [`vercel.json`](file:///c:/Users/sksha/OneDrive/Desktop/Grounded-Advisory-Assistant-GAA/vercel.json):

```
├── frontend/               # Next.js 14 App Router (TailwindCSS, Lucide)
├── backend/                # FastAPI RAG Engine (Groq LLM, ChromaDB, SQLAlchemy)
│   ├── api/index.py        # Python Serverless entrypoint
│   └── requirements.txt    # Backend Python dependencies
├── api/                    # Root Python Serverless fallback
│   ├── index.py
│   └── requirements.txt
└── vercel.json             # Service routing & edge rewrites
```

- Requests to `/api/*` are routed directly to the FastAPI backend service (`backend/api/index.py`).
- All other routes (`/*`) are served by the Next.js frontend (`frontend/`).
- In the browser, API calls dynamically use relative `/api/v1/...` in production, eliminating CORS and hardcoded `localhost` issues.

---

## Step-by-Step Vercel Deployment

### 1. Push Code to GitHub
Ensure the latest code on your branch is pushed:
```bash
git push origin feat/production-readiness-and-cleanup
```

### 2. Import Project in Vercel
1. Log in to [vercel.com](https://vercel.com).
2. Click **"Add New..."** -> **"Project"**.
3. Select your repository: `kalviumcommunity/S84_0826_VectorVest_Grounded-Advisory-Assistant-GAA-`.
4. Leave **Root Directory** as `./` (default root).
5. Vercel automatically detects [`vercel.json`](file:///c:/Users/sksha/OneDrive/Desktop/Grounded-Advisory-Assistant-GAA/vercel.json) with dual `frontend` and `backend` services.

### 3. Configure Environment Variables
In the Vercel deployment modal (or under **Settings -> Environment Variables**), configure the following keys:

| Variable Name | Required | Description / Example Value |
|---|---|---|
| `DATABASE_URL` | **Yes** | NeonDB PostgreSQL connection string: `postgresql://neondb_owner:...@ep-mute-lab-b5s1mquk-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require` |
| `GROQ_API_KEY` | **Yes** | Your Groq API key: `gsk_...` |
| `JWT_SECRET_KEY` | **Yes** | 64-character hexadecimal key (e.g. `openssl rand -hex 32` or your existing secret) |
| `ENVIRONMENT` | Optional | `production` |
| `SIMILARITY_THRESHOLD` | Optional | `0.50` (calibrated for high precision retrieval) |
| `GROQ_MODEL` | Optional | `openai/gpt-oss-20b` (or `llama-3.3-70b-versatile`) |

> [!NOTE]
> `NEXT_PUBLIC_API_URL` is **not required** when deploying as a fullstack project on Vercel, because the frontend automatically routes to `/api/v1` on the same domain via Vercel's edge rewrites.

### 4. Deploy
Click **"Deploy"**. Vercel will:
1. Build the Next.js static and dynamic assets (`frontend/`).
2. Package the Python FastAPI serverless runtime (`backend/`).
3. Deploy both services together with unified routing.

---

## Verifying the Deployment

1. **System Health & APIs:**
   - Health check: `https://<your-project>.vercel.app/health`
   - API info: `https://<your-project>.vercel.app/api`
   - Swagger OpenAPI Docs: `https://<your-project>.vercel.app/docs`

2. **Default Seed Credentials:**
   - **Relationship Manager:** `rm@wealth.bank.com` / `AdvisoryPass2024!`
   - **Compliance Officer:** `compliance@wealth.bank.com` / `AuditSecure2024!`
   - **North Regional RM:** `rm_north@wealth.bank.com` / `NorthPass2024!`

3. **Verify Capability & Greeting Handling:**
   - Ask: *"how can you help me"*
   - WealthGuard will return its structured capabilities and suggested policy prompts instead of triggering a compliance refusal.

4. **Verify Zero-Hallucination Policy Retrieval:**
   - Ask: *"What is the capital gains tax offset for municipal bonds under 2024 rules?"*
   - WealthGuard will retrieve the verified clause citations with clickable badges and grounded answers.
