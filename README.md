# AI Agent Creator Platform

**Build, deploy, and manage AI agents with 30+ tool integrations.**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-blue.svg)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ed.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Live app](http://www..com/)

This system lets users create AI agents in plain language (or from templates), connect them to tools like Gmail, Slack, and GitHub, chat with them in real time, and automate them with scheduled or event-based triggers.

---

## Features

- **Agent builder** — create agents from a natural-language description, a 4-step wizard, or 27 templates across 9 categories
- **Real-time chat** — streaming responses over Server-Sent Events, including live tool-call status
- **30+ integrations** — Gmail, Slack, GitHub, Google Drive, Notion, HubSpot, and more via Composio OAuth
- **Built-in tools** — weather, calculator, stock quotes, YouTube search, web search, website reader
- **Workflow automation** — visual workflow builder (React Flow) with cron, app-event, and manual triggers
- **Telegram bots** — connect any agent to a Telegram bot
- **Auth** — JWT in HttpOnly cookies, Google and GitHub OAuth, email verification
- **Credit system** — per-action usage tracking with a monthly refresh

---

## Tech stack

| Layer | Technologies |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui, Zustand, TanStack Query, React Flow |
| Backend | Django 4.2, Django REST Framework, Gunicorn, drf-spectacular (OpenAPI) |
| AI | OpenAI API (function calling), Composio |
| Data | PostgreSQL (Supabase) in production, SQLite in development |
| Infra | Docker Compose, Nginx reverse proxy, AWS EC2, Let's Encrypt |

---

## Architecture

```
User → React frontend (Nginx)
          │
          ├── static files  /, /assets/*
          │
          └── /api/*  →  Django backend (Gunicorn)
                              │
                ┌─────────────┼─────────────┐
                ↓             ↓             ↓
           PostgreSQL     OpenAI API    Composio API
                                            ↓
                                   30+ third-party apps
```

**How a chat message flows:**

1. The frontend opens an SSE stream to `POST /api/agents/{id}/chat/`.
2. The backend sends the conversation and the agent's tools to OpenAI.
3. When the model calls a tool, the backend runs it (built-in or via Composio) and streams `tool_call_start` / `tool_call_result` events.
4. The final answer streams back word by word as `content_delta` events and is saved to the database.

---

## Getting started

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker and Docker Compose (for containerized runs)
- API keys: OpenAI and Composio (required); YouTube, SerpAPI, Google/GitHub OAuth, EmailJS (optional)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in your keys
python manage.py migrate
python manage.py seed_agent_templates   # optional
python manage.py runserver
```

Runs at `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env            # set VITE_API_URL=http://localhost:8000
npm run dev
```

Runs at `http://localhost:5173`.

### Run everything with Docker

```bash
docker compose up -d --build
docker compose exec backend python manage.py migrate
```

App at `http://localhost`, API at `http://localhost/api/`.

---

## Environment variables

Copy `backend/.env.example` to `backend/.env`. Never commit real values.

| Variable | Required | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | Yes | Django secret key |
| `DEBUG` | Yes | `True` in development, `False` in production |
| `ALLOWED_HOSTS` | Yes | Comma-separated hostnames, e.g. `localhost,yourdomain.com` |
| `CORS_ALLOWED_ORIGINS` | Yes | e.g. `http://localhost:5173,https://yourdomain.com` |
| `FRONTEND_URL` | Yes | Frontend base URL |
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `COMPOSIO_API_KEY` | Yes | Composio API key |
| `DATABASE_URL` | Production | PostgreSQL connection string |
| `YOUTUBE_API_KEY` | No | YouTube search tool |
| `SERPAPI_KEY` | No | Web search tool |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | No | Google login |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | No | GitHub login |
| `EMAILJS_*` | No | Verification and password-reset emails |
| `ADMIN_URL` | No | Custom Django admin path |

Frontend (`frontend/.env`): `VITE_API_URL` (required), `VITE_WEBSOCKET_URL` (optional).

---

## Deployment

The app is deployed to AWS EC2 with Docker Compose behind Nginx.

1. Provision an EC2 instance with Docker installed and ports 80/443 open.
2. Create `backend/.env` with production values (`DEBUG=False`, real `ALLOWED_HOSTS`, `DATABASE_URL`).
3. Run `./ec2-management.sh` (after setting your own server host and SSH key in the script). It builds the frontend, uploads the bundle, builds the containers, runs migrations, collects static files, and runs health checks.
4. Add HTTPS with Certbot: `sudo certbot --nginx -d yourdomain.com`.

---

## API

Interactive docs are generated with drf-spectacular:

- Swagger UI: `/api/docs/`
- ReDoc: `/api/docs/redoc/`
- OpenAPI schema: `/api/schema/`

Main resources:

| Resource | Endpoints |
|---|---|
| Auth | register, login, logout, me, password reset, email verification, Google/GitHub OAuth |
| Agents | CRUD, `chat/` (SSE), `messages/`, `tools/`, Telegram connect/disconnect |
| Templates | list, instantiate |
| Connections | list, authenticate, callback, disconnect |
| Workflows and triggers | CRUD |
| Files | upload, download, delete |
| Credits | balance, history |

---

## Project structure

```
├── backend/
│   ├── api_agents/          # Main app: models, views, agent logic, tools, SSE, credits
│   ├── config/              # Django settings and URLs
│   ├── endpoints/           # API docs (markdown)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/      # Layout, pages (builder, chat, agents, workflows…), shared UI
│       └── lib/             # API client and utils
├── nginx/conf.d/            # Reverse proxy config
├── docker-compose.yml
└── ec2-management.sh
```

---

## Security notes

- JWT stored in HttpOnly cookies, CSRF protection enabled
- OAuth tokens for third-party apps are handled by Composio, not stored in plain text
- Containers run as a non-root user
- Secrets live only in `.env` files, which are git-ignored

---

## License

MIT — see [LICENSE](LICENSE).

Questions or bugs: [open an issue](https://github.com/shaharishay14/Autonomous-Agents/issues).
