# GuruSikshan — AI Personalization Service

Python service that powers authenticated public chat, retrieval, and personalization workflows for the GuruSikshan platform. It sits behind the main backend API and connects to Supabase and RAGFlow.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Runtime | Python |
| Auth | JWT + custom client auth |
| Vector Store | ChromaDB |
| AI / RAG | RAGFlow |
| Database | Supabase |
| Containerization | Docker |

---

## What It Does

- Handles public auth and chat routes for the AI layer.
- Adds request authentication, audit logging, and rate limiting.
- Integrates with RAGFlow for retrieval and document workflows.
- Supports lesson-planning related AI features.
- Uses Supabase from the backend only, not from the browser.

---

## Project Structure

```text
Backend/
└── ai-personalization/
    ├── chroma_db/
    ├── src/
    │   ├── auth/
    │   │   ├── client_auth.py
    │   │   └── token_utils.py
    │   ├── middleware/
    │   │   ├── audit_logger.py
    │   │   ├── auth_middleware.py
    │   │   └── rate_limiter.py
    │   ├── routes/
    │   │   ├── public_auth_routes.py
    │   │   └── public_chat_routes.py
    │   ├── scripts/
    │   │   └── create_client.py
    │   ├── uploads/
    │   ├── app.py
    │   ├── lesson_planner_routes.py
    │   ├── ragflow_client.py
    │   ├── ragflow_routes.py
    │   ├── resource_registry.py
    │   └── supabase_client.py
    ├── Dockerfile
    ├── requirements.txt
    └── README.md
```

---

## How It Fits

```text
Frontend → Backend API → AI Personalization → Supabase / RAGFlow
```

The backend proxies `/api/public` traffic to `AI_SERVICE_URL`, which defaults to `http://localhost:5001`. In Docker, this service should be reachable through the Compose service name, not `localhost`.

---

## Run With Docker

This is the intended way to run the full platform from the repo root:

```bash
docker compose up --build
```

No separate service-local env file is needed if your root `docker-compose.yml` already reads the root `.env`. The AI service should keep listening on port `5001` so the backend proxy works as expected.

---

## Run Locally

If you want to run only this service for development:

```bash
cd Backend/ai-personalization
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd src
python app.py
```

Keep the service on port `5001` so the backend integration remains unchanged.

---

## Main Modules

### `src/app.py`
Application entry point for starting the service.

### `src/routes/public_auth_routes.py`
Public auth routes for client-facing access to the AI layer.

### `src/routes/public_chat_routes.py`
Public chat endpoints used through the backend proxy.

### `src/auth/`
Client authentication helpers and token utilities.

### `src/middleware/`
Auth enforcement, audit logging, and rate limiting.

### `src/ragflow_client.py` and `src/ragflow_routes.py`
RAGFlow integration for retrieval and AI workflows.

### `src/supabase_client.py`
Server-side Supabase connection setup.

### `src/lesson_planner_routes.py`
Lesson-planning related AI functionality.

### `src/scripts/create_client.py`
Utility for creating seeded or onboarding client accounts.

---

## Quick Start

```bash
# from repo root
docker compose up --build

# or run only the service
cd Backend/ai-personalization
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd src
python app.py
```
