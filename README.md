# KGen21 - AI Agent Creator Platform

<div align="center">

**Build, Deploy, and Manage AI Agents with 30+ Tool Integrations**

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Django](https://img.shields.io/badge/Django-4.2+-green.svg)
![React](https://img.shields.io/badge/React-19-61dafb.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.9-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ed.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

[Live App](http://www.kgen21.com/)

</div>

---

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Docker Deployment](#docker-deployment)
- [EC2 Production Deployment](#ec2-production-deployment)
- [Updating the Application](#updating-the-application)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Database](#database)
- [Features In-Depth](#features-in-depth)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)
- [Useful Commands](#useful-commands)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Agent Builder** - Create AI agents with natural language or templates
- **Real-time Chat** - SSE streaming conversations with AI agents
- **30+ Tool Integrations** - Connect to Gmail, Slack, GitHub, Google Drive, and more via Composio
- **Custom Tools** - Built-in tools (weather, calculator, stocks, YouTube, web search)
- **Workflow Automation** - Visual workflow builder with triggers (scheduled, event-based)
- **Telegram Integration** - Connect agents to Telegram bots
- **Social OAuth** - Google and GitHub authentication
- **Credit System** - Monthly credit refresh (100 credits/month)
- **Agent Templates** - 27 pre-built templates across 9 categories
- **File Attachments** - Upload and attach files to conversations
- **Public Sharing** - Share agents publicly
- **Email Verification** - Secure account verification

---

## Technology Stack

### Frontend
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS 4 + shadcn/ui components
- **State Management**: Zustand + TanStack Query (React Query)
- **Routing**: React Router v7
- **HTTP Client**: Axios
- **Forms**: React Hook Form + Yup validation
- **Real-time**: SSE (Server-Sent Events) for streaming
- **Animations**: Framer Motion
- **Markdown**: React Markdown with GitHub-flavored markdown

### Backend
- **Framework**: Django 4.2
- **API**: Django REST Framework 3.14
- **Database**: PostgreSQL (Supabase) / SQLite (development)
- **Authentication**: JWT (HttpOnly cookies) + django-allauth (OAuth)
- **AI Integration**: OpenAI API + Composio
- **WSGI Server**: Gunicorn (3 workers)
- **API Documentation**: drf-spectacular (OpenAPI 3.0)
- **Other Tools**: yfinance, BeautifulSoup4, QRCode

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Web Server**: Nginx (reverse proxy)
- **Deployment**: AWS EC2
- **SSL**: Let's Encrypt (configured)

---

## Architecture

### System Flow
```
User → React Frontend (Nginx:80)
          ↓
      [Static Files: /, /assets/*]
          ↓
      [API Routes: /api/*] → Django Backend (Gunicorn:8000)
                                    ↓
                      ┌─────────────┼─────────────┐
                      ↓             ↓             ↓
                  PostgreSQL    OpenAI API    Composio API
                  (Supabase)                      ↓
                                          30+ Third-Party Apps
                                          (Gmail, Slack, GitHub, etc.)
```

### Container Architecture
```
docker-compose.yml
├── nginx (Port 80, 443)
│   ├── Serves React app (/)
│   ├── Proxies API (/api/*)
│   └── Handles static files
│
└── backend (Port 8000 - internal)
    ├── Django + DRF
    ├── Gunicorn WSGI
    └── Health checks
```

---

## Prerequisites

### Required Software
- **Node.js**: 18+ (for frontend development)
- **Python**: 3.12+ (for backend development)
- **PostgreSQL**: 14+ (production) or SQLite (development)
- **Docker**: 20+ and Docker Compose (for containerized deployment)
- **Git**: Version control

### Required API Keys
- **OpenAI API Key** - For AI agent functionality
- **Composio API Key** - For tool integrations
- **YouTube API Key** - For YouTube search tool
- **SerpAPI Key** - For web search tool
- **Google OAuth Credentials** - For Google login
- **GitHub OAuth Credentials** - For GitHub login
- **EmailJS Credentials** - For email notifications

---

## Quick Start

### Development Setup (Without Docker)

#### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd KGen21
```

#### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your API keys and credentials

# Run database migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Seed agent templates (optional)
python manage.py seed_agent_templates

# Run development server
python manage.py runserver
```

Backend will be available at: `http://localhost:8000`

#### 3. Frontend Setup
```bash
# Open new terminal
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env
# Edit .env with VITE_API_URL=http://localhost:8000

# Run development server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

---

## Environment Variables

### Backend (.env)

Create `backend/.env` from `backend/.env.example`:

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | Yes | `your-secret-key-here` |
| `DEBUG` | Debug mode | Yes | `True` (dev), `False` (prod) |
| `ALLOWED_HOSTS` | Allowed hostnames | Yes | `localhost,127.0.0.1,13.62.63.125` |
| `DATABASE_URL` | PostgreSQL connection | Production | `postgresql://user:pass@host:5432/db` |
| `CORS_ALLOWED_ORIGINS` | CORS whitelist | Yes | `http://localhost:5173,http://13.62.63.125` |
| `OPENAI_API_KEY` | OpenAI API key | Yes | `sk-...` |
| `COMPOSIO_API_KEY` | Composio API key | Yes | `your-composio-key` |
| `YOUTUBE_API_KEY` | YouTube Data API v3 | Optional | `your-youtube-key` |
| `SERPAPI_KEY` | SerpAPI for web search | Optional | `your-serpapi-key` |
| `GOOGLE_CLIENT_ID` | Google OAuth | Optional | `your-client-id.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth secret | Optional | `your-secret` |
| `GITHUB_CLIENT_ID` | GitHub OAuth | Optional | `your-github-client-id` |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth secret | Optional | `your-github-secret` |
| `EMAILJS_SERVICE_ID` | EmailJS service | Optional | `service_...` |
| `EMAILJS_TEMPLATE_ID` | Email template | Optional | `template_...` |
| `EMAILJS_PASSWORD_RESET_TEMPLATE_ID` | Password reset template | Optional | `template_...` |
| `EMAILJS_PUBLIC_KEY` | EmailJS public key | Optional | `your-public-key` |
| `EMAILJS_PRIVATE_KEY` | EmailJS private key | Optional | `your-private-key` |
| `FRONTEND_URL` | Frontend URL | Yes | `http://localhost:5173` |
| `ADMIN_URL` | Custom admin path | Optional | `admin-secure-2024/` |

### Frontend (.env)

Create `frontend/.env`:

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `VITE_API_URL` | Backend API URL | Yes | `http://localhost:8000` |
| `VITE_WEBSOCKET_URL` | WebSocket URL | Optional | `ws://localhost:8000` |

---

## Docker Deployment

### Local Docker Deployment

Use the automated deployment script:

```bash
# Make script executable (first time only)
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

**What the script does:**
1. Checks for `backend/.env` file
2. Builds frontend (`npm run build:prod`)
3. Builds Docker images
4. Stops existing containers
5. Starts new containers
6. Runs database migrations
7. Collects static files
8. Performs health checks

**Access your application:**
- Frontend: http://localhost/
- API: http://localhost/api/
- Admin: http://localhost/admin/

### Manual Docker Commands

```bash
# Build and start containers
docker compose up -d --build

# View logs
docker compose logs -f

# Stop containers
docker compose down

# Restart containers
docker compose restart

# Enter backend container
docker compose exec backend bash

# Run Django commands
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py collectstatic
```

---

## EC2 Production Deployment

### Automated Deployment to EC2

**Server Details:**
- **IP**: 13.62.63.125
- **User**: ubuntu
- **PEM File**: `~/Downloads/kgen.pem`
- **Remote Directory**: `/home/ubuntu/KGen21`

#### Step 1: Prepare Deployment

```bash
# Ensure you have the PEM file
ls ~/Downloads/kgen.pem

# Set correct permissions
chmod 400 ~/Downloads/kgen.pem

# Create backend/.env with production credentials
cp backend/.env.example backend/.env
# Edit backend/.env with production values
```

#### Step 2: Run Deployment Script

```bash
# Make script executable (first time only)
chmod +x deploy-to-ec2.sh

# Deploy to EC2
./deploy-to-ec2.sh
```

**What the script does:**
1. Checks for PEM file and .env
2. Builds frontend (`npm run build:prod`)
3. Creates directory on EC2
4. Creates tar archive (excludes node_modules, .git, etc.)
5. Uploads via SCP to EC2
6. Extracts files on server
7. Installs Docker if needed
8. Builds Docker images on EC2
9. Runs containers
10. Executes migrations
11. Collects static files
12. Performs health checks

**Access your production application:**
- Frontend: http://13.62.63.125/
- API: http://13.62.63.125/api/
- Admin: http://13.62.63.125/admin/

### Manual EC2 Deployment

If you prefer manual deployment:

#### Step 1: Build Frontend
```bash
cd frontend
npm install
npm run build:prod
cd ..
```

#### Step 2: Upload to EC2
```bash
# Create tar archive
tar -czf kgen21-deploy.tar.gz \
    --exclude=node_modules \
    --exclude=.git \
    --exclude=venv \
    --exclude=__pycache__ \
    backend \
    frontend/dist \
    nginx \
    docker-compose.yml

# Upload to EC2
scp -i ~/Downloads/kgen.pem kgen21-deploy.tar.gz ubuntu@13.62.63.125:/home/ubuntu/

# Clean up local tar
rm kgen21-deploy.tar.gz
```

#### Step 3: Deploy on EC2
```bash
# SSH into EC2
ssh -i ~/Downloads/kgen.pem ubuntu@13.62.63.125

# Extract files
cd /home/ubuntu
mkdir -p KGen21
cd KGen21
tar -xzf ../kgen21-deploy.tar.gz
rm ../kgen21-deploy.tar.gz

# Build and run containers
sudo docker compose down
sudo docker compose build
sudo docker compose up -d

# Run migrations
sudo docker compose exec -T backend python manage.py migrate --noinput

# Collect static files
sudo docker compose exec -T backend python manage.py collectstatic --noinput

# Check status
sudo docker compose ps
sudo docker compose logs -f
```

---

## Updating the Application

### A. Updating Backend Code

#### Using Automated Script (Recommended)
```bash
# 1. Make changes to backend code
# 2. Test locally
cd backend
python manage.py runserver

# 3. Deploy to EC2 (includes backend + frontend)
cd ..
./deploy-to-ec2.sh
```

#### Manual Backend Update
```bash
# 1. Make changes locally and test

# 2. Upload backend files to EC2
cd backend
scp -i ~/Downloads/kgen.pem -r . ubuntu@13.62.63.125:/home/ubuntu/KGen21/backend/

# 3. SSH to EC2 and update
ssh -i ~/Downloads/kgen.pem ubuntu@13.62.63.125
cd /home/ubuntu/KGen21

# 4. Run migrations if needed
sudo docker compose exec backend python manage.py migrate

# 5. Restart backend container
sudo docker compose restart backend

# 6. Check logs
sudo docker compose logs -f backend
```

#### Backend-Only Quick Update (No Docker Rebuild)
```bash
# If only Python code changed (no requirements.txt update)
ssh -i ~/Downloads/kgen.pem ubuntu@13.62.63.125
cd /home/ubuntu/KGen21

# Copy new files into running container
sudo docker compose cp backend/api_agents ubuntu@13.62.63.125:/app/api_agents

# Restart backend
sudo docker compose restart backend
```

### B. Updating Frontend Code

#### Using Automated Script (Recommended)
```bash
# 1. Make changes to frontend code
# 2. Test locally
cd frontend
npm run dev

# 3. Deploy to EC2
cd ..
./deploy-to-ec2.sh  # Builds and deploys both backend + frontend
```

#### Manual Frontend Update
```bash
# 1. Build production bundle
cd frontend
npm run build:prod

# 2. Upload to EC2
scp -i ~/Downloads/kgen.pem -r dist ubuntu@13.62.63.125:/home/ubuntu/KGen21/frontend/

# 3. Restart nginx
ssh -i ~/Downloads/kgen.pem ubuntu@13.62.63.125
cd /home/ubuntu/KGen21
sudo docker compose restart nginx

# 4. Clear browser cache and test
```

### C. Updating Docker Containers (Full Rebuild)

When you update:
- Python dependencies (`requirements.txt`)
- Node dependencies (`package.json`)
- Dockerfile or docker-compose.yml
- nginx configuration

```bash
# SSH to EC2
ssh -i ~/Downloads/kgen.pem ubuntu@13.62.63.125
cd /home/ubuntu/KGen21

# Stop all containers
sudo docker compose down

# Rebuild images from scratch
sudo docker compose build --no-cache

# Start containers
sudo docker compose up -d

# Wait for services to be healthy (30-40 seconds)
sleep 40

# Run migrations
sudo docker compose exec backend python manage.py migrate --noinput

# Collect static files
sudo docker compose exec backend python manage.py collectstatic --noinput

# Check container status
sudo docker compose ps

# View logs
sudo docker compose logs -f

# Health check
curl http://localhost/health
curl http://localhost/api/
```

### D. Quick Update Commands Reference

```bash
# Restart specific service
sudo docker compose restart backend
sudo docker compose restart nginx

# Restart all services (no rebuild)
sudo docker compose restart

# View logs
sudo docker compose logs -f                # All services
sudo docker compose logs -f backend        # Backend only
sudo docker compose logs -f nginx          # Nginx only
sudo docker compose logs --tail=100        # Last 100 lines

# Enter backend container
sudo docker compose exec backend bash

# Run Django management commands
sudo docker compose exec backend python manage.py migrate
sudo docker compose exec backend python manage.py createsuperuser
sudo docker compose exec backend python manage.py shell
sudo docker compose exec backend python manage.py seed_agent_templates

# Check container status and health
sudo docker compose ps
sudo docker stats

# Remove stopped containers and unused images
sudo docker compose down
sudo docker system prune -a

# Update only environment variables (no code change)
# 1. Edit backend/.env on EC2
sudo nano /home/ubuntu/KGen21/backend/.env
# 2. Restart backend
sudo docker compose restart backend
```

### E. Database Migrations

```bash
# Create new migration (development)
cd backend
python manage.py makemigrations

# Apply migrations (production)
ssh -i ~/Downloads/kgen.pem ubuntu@13.62.63.125
cd /home/ubuntu/KGen21
sudo docker compose exec backend python manage.py migrate

# View migration status
sudo docker compose exec backend python manage.py showmigrations

# Rollback migration (if needed)
sudo docker compose exec backend python manage.py migrate api_agents 0012_previous_migration
```

### F. Zero-Downtime Deployment Tips

For production with active users:

```bash
# 1. Build new images without stopping services
sudo docker compose build

# 2. Use rolling restart (one service at a time)
sudo docker compose up -d --no-deps --build backend
# Wait 30 seconds
sudo docker compose up -d --no-deps --build nginx

# 3. Run migrations during low-traffic periods
# Migrations run fast, but plan accordingly
```

---

## Project Structure

```
KGen21/
├── backend/                          # Django REST API
│   ├── api_agents/                   # Main Django app
│   │   ├── migrations/               # Database migrations (13 files)
│   │   ├── management/               # Custom commands
│   │   │   └── commands/
│   │   │       ├── seed_agent_templates.py
│   │   │       └── sync_composio_apps.py
│   │   ├── models.py                 # Database models (User, Agent, etc.)
│   │   ├── views.py                  # API endpoints (5,118 lines)
│   │   ├── serializers.py            # DRF serializers (670 lines)
│   │   ├── urls.py                   # URL routing
│   │   ├── admin.py                  # Django admin config
│   │   ├── auth.py                   # JWT authentication
│   │   ├── social_auth_views.py      # OAuth views
│   │   ├── agent_service.py          # AI agent logic (1,092 lines)
│   │   ├── agent_tools_service.py    # Custom tools (548 lines)
│   │   ├── agent_tools_config.py     # Tool definitions
│   │   ├── composio_config.py        # Composio apps config
│   │   ├── credits.py                # Credit system
│   │   ├── streaming_utils.py        # SSE utilities
│   │   ├── telegram_utils.py         # Telegram integration
│   │   ├── spectacular_extensions.py # API docs
│   │   └── spectacular_suppress.py   # API docs suppression
│   ├── config/                       # Django project settings
│   │   ├── settings.py               # Main configuration
│   │   ├── urls.py                   # Root URL config
│   │   ├── wsgi.py                   # WSGI application
│   │   └── asgi.py                   # ASGI application
│   ├── endpoints/                    # API documentation (markdown)
│   │   ├── README.md
│   │   ├── auth.md
│   │   ├── agents.md
│   │   ├── connections.md
│   │   ├── files.md
│   │   ├── triggers.md
│   │   ├── workflows.md
│   │   └── csrf.md
│   ├── requirements.txt              # Python dependencies
│   ├── Dockerfile                    # Backend container
│   ├── .dockerignore                 # Docker exclusions
│   ├── .env.example                  # Environment template
│   ├── manage.py                     # Django CLI
│   ├── auth_configs.json             # Composio OAuth configs
│   ├── setup_oauth.py                # OAuth setup helper
│   ├── fetch_triggers.py             # Trigger fetcher
│   ├── schema.yml                    # OpenAPI schema
│   └── FRONTEND_SSE_GUIDE.md         # SSE integration guide
│
├── frontend/                         # React + TypeScript
│   ├── src/
│   │   ├── main.tsx                  # Entry point
│   │   ├── App.tsx                   # Root component
│   │   ├── components/
│   │   │   ├── layout/               # Layout components
│   │   │   │   ├── Layout.tsx
│   │   │   │   ├── Nav.tsx
│   │   │   │   └── Chatbot.tsx
│   │   │   ├── pages/                # Page components
│   │   │   │   ├── auth/             # Authentication
│   │   │   │   ├── builder/          # Agent builder (homepage)
│   │   │   │   ├── agents/           # Agent management
│   │   │   │   ├── chat/             # Chat interface
│   │   │   │   ├── integrations/     # Tool integrations
│   │   │   │   ├── workflows/        # Workflow automation
│   │   │   │   ├── settings/         # User settings
│   │   │   │   └── public/           # Public pages
│   │   │   ├── router/               # Routing config
│   │   │   └── shared/               # Shared components
│   │   └── lib/
│   │       ├── axios.ts              # API client
│   │       └── utils.ts              # Utilities
│   ├── public/                       # Static assets
│   ├── dist/                         # Build output
│   ├── package.json                  # Dependencies
│   ├── vite.config.ts                # Vite config
│   ├── tsconfig.json                 # TypeScript config
│   ├── tailwind.config.ts            # Tailwind config
│   ├── components.json               # shadcn/ui config
│   └── .env                          # Environment variables
│
├── nginx/                            # Nginx configuration
│   └── conf.d/
│       └── app.conf                  # Reverse proxy config
│
├── docker-compose.yml                # Multi-container orchestration
├── deploy.sh                         # Local deployment script
├── deploy-to-ec2.sh                  # EC2 deployment script
├── DEPLOYMENT.md                     # Deployment guide
├── DOCKER_SETUP.md                   # Docker setup guide
└── README.md                         # This file
```

---

## API Documentation

### Interactive Documentation

- **Swagger UI**: http://13.62.63.125/api/docs/
- **ReDoc**: http://13.62.63.125/api/docs/redoc/
- **OpenAPI Schema**: http://13.62.63.125/api/schema/

### Authentication

**JWT with HttpOnly Cookies:**
- Access token stored in `access` cookie
- Refresh token stored in `refresh` cookie
- Automatic token refresh on API calls
- CSRF protection enabled

**OAuth Providers:**
- Google OAuth 2.0
- GitHub OAuth

### Key Endpoints

#### Authentication
```
POST   /api/auth/register/           - User registration
POST   /api/auth/login/              - Login (sets JWT cookies)
POST   /api/auth/logout/             - Logout (clears cookies)
GET    /api/auth/me/                 - Current user info
POST   /api/auth/password/forgot/    - Password reset request
POST   /api/auth/password/reset/     - Password reset confirm
POST   /api/auth/email/verify/       - Email verification
POST   /api/auth/email/resend/       - Resend verification
GET    /api/auth/google/             - Google OAuth
GET    /api/auth/github/             - GitHub OAuth
GET    /api/auth/github/callback/    - GitHub callback
```

#### Agents
```
GET    /api/agents/                  - List user agents
POST   /api/agents/                  - Create agent
GET    /api/agents/{id}/             - Get agent details
PUT    /api/agents/{id}/             - Update agent
DELETE /api/agents/{id}/             - Delete agent
POST   /api/agents/{id}/chat/        - Chat with agent (SSE streaming)
GET    /api/agents/{id}/messages/    - Get chat history
POST   /api/agents/{id}/tools/       - Add/remove tools
POST   /api/agents/{id}/telegram/connect/    - Connect Telegram bot
POST   /api/agents/{id}/telegram/disconnect/ - Disconnect Telegram bot
```

#### Agent Templates
```
GET    /api/agent-templates/         - List templates
POST   /api/agent-templates/{id}/instantiate/ - Create from template
```

#### Connections (Tool Integrations)
```
GET    /api/connections/             - List active connections
POST   /api/connections/authenticate_tool/ - Start OAuth flow
POST   /api/connections/callback/    - OAuth callback
GET    /api/connections/check_connections/ - Check connection status
DELETE /api/connections/{id}/disconnect/ - Disconnect tool
```

#### Files
```
GET    /api/files/                   - List user files
POST   /api/files/                   - Upload file
GET    /api/files/{id}/download/     - Download file
DELETE /api/files/{id}/              - Delete file
```

#### Workflows
```
GET    /api/workflows/               - List workflows
POST   /api/workflows/               - Create workflow
GET    /api/workflows/{id}/          - Get workflow
PUT    /api/workflows/{id}/          - Update workflow
DELETE /api/workflows/{id}/          - Delete workflow
```

#### Triggers
```
GET    /api/triggers/                - List triggers
POST   /api/triggers/                - Create trigger
GET    /api/triggers/{id}/           - Get trigger
PUT    /api/triggers/{id}/           - Update trigger
DELETE /api/triggers/{id}/           - Delete trigger
```

#### Credits
```
GET    /api/credits/balance/         - Current credit balance
GET    /api/credits/history/         - Usage history
POST   /api/credits/add/             - Add credits (admin only)
```

### Rate Limiting

Credit costs per action:
- **Message**: 1 credit
- **Tool call**: 2 credits
- **File upload**: 5 credits
- Monthly refresh: 100 credits on the 1st of each month

---

## Database

### Models Overview

**User** - Custom user model with credit system
- UUID primary key
- Email, password, name
- `total_credits`, `credits_used`, `credit_refresh_date`
- Auto-refresh 100 credits/month

**UserProfile** - Extended user info
- Email verification status
- Verification token and expiry

**Agent** - AI agents
- Name, prompt, avatar (binary)
- Tools, app_connections, agent_tools (JSON)
- Belongs to user

**AgentTemplate** - Pre-built templates
- 9 categories: research, project_mgmt, developer, communication, marketing, ecommerce, health, education, entertainment
- 27 total templates

**ChatMessage** - Conversation history
- Agent, role (user/assistant/system), content
- File attachments (JSON)
- Timestamp

**FileAttachment** - File uploads
- Binary storage in database
- MIME type, size, filename
- Agent-specific or temporary

**ComposioConnection** - OAuth connections
- Tool name, auth config ID, connection ID
- Soft delete support (`deleted_at`)

**Trigger** - Automation triggers
- Types: scheduled (cron), event-based (app events), manual
- Agent, command, schedule/trigger_id, output_type

**TriggerExecution** - Trigger logs
- Execution status, result, timestamp

**Workflow** - Visual workflows
- React Flow format: nodes, edges, viewport (JSON)

**WorkflowExecution** - Workflow logs
- Execution status, result, timestamp

**MessagingChannel** - Multi-channel support
- Telegram, WhatsApp
- Channel type, external ID, config

**MessagingSession** - External conversations
- Session ID, platform data

**UsageLog** - Credit usage tracking
- User, action type, credits used, timestamp

### Database Commands

```bash
# Create migrations (development)
cd backend
python manage.py makemigrations

# Apply migrations (production)
ssh -i ~/Downloads/kgen.pem ubuntu@13.62.63.125
cd /home/ubuntu/KGen21
sudo docker compose exec backend python manage.py migrate

# Check migration status
sudo docker compose exec backend python manage.py showmigrations

# Create database backup (PostgreSQL)
pg_dump -U username -d dbname > backup.sql

# Restore database
psql -U username -d dbname < backup.sql

# Django admin - create superuser
sudo docker compose exec backend python manage.py createsuperuser

# Seed agent templates
sudo docker compose exec backend python manage.py seed_agent_templates

# Django shell
sudo docker compose exec backend python manage.py shell
```

---

## Features In-Depth

### 1. Agent Builder

**Natural Language Creation:**
- User describes desired agent in plain language
- AI generates agent name, prompt, and selects relevant tools
- Automatic avatar assignment

**Manual Creation:**
- 4-step wizard:
  1. Basic info (name, prompt)
  2. Tool selection (Composio apps)
  3. Agent tools (custom tools)
  4. Triggers (optional)

**Template-Based:**
- 27 pre-built templates across 9 categories
- One-click instantiation
- Templates include optimized prompts and pre-selected tools

### 2. Real-time Chat with SSE Streaming

**Technology:** Server-Sent Events (SSE)

**Event Types:**
- `status` - Agent status (thinking, tool_calling, generating)
- `tool_call_start` - Tool execution started
- `tool_call_result` - Tool execution result
- `content_delta` - Partial response text (streaming word by word)
- `message_complete` - Message saved to database
- `done` - Stream finished
- `error` - Error occurred
- `heartbeat` - Keep-alive signal

**Frontend Implementation:**
```typescript
import { fetchEventSource } from '@microsoft/fetch-event-source';

await fetchEventSource(`${API_URL}/api/agents/${agentId}/chat/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: 'Hello!', file_attachments: [] }),
  onmessage(event) {
    const data = JSON.parse(event.data);
    // Handle: status, content_delta, tool_call_start, etc.
  }
});
```

### 3. Tool Integrations (30+ Apps via Composio)

**Productivity:**
- Gmail, Google Drive, Google Docs, Sheets, Calendar
- Outlook, OneDrive, Office 365

**Communication:**
- Slack, Microsoft Teams, Zoom, Google Meet
- WhatsApp, Telegram

**Project Management:**
- Asana, ClickUp, Monday, Todoist, Linear, Trello

**Development:**
- GitHub, GitLab, Figma, Jira

**Social Media:**
- Twitter, LinkedIn, Instagram, Facebook, Reddit

**Business:**
- Stripe, Shopify, Notion, Airtable, Canva, HubSpot

**Storage:**
- Dropbox, Box

**OAuth Flow:**
1. User clicks "Connect" on tool
2. Backend creates Composio auth session
3. User authorizes in popup
4. Composio redirects to callback
5. Backend stores connection

### 4. Custom Agent Tools (No OAuth Required)

**Available Tools:**
- `weather` - Current weather for any location (Open-Meteo API)
- `calculator` - Mathematical calculations
- `yahoo_finance` - Stock quotes and financial data (yfinance)
- `youtube` - Search YouTube videos (YouTube Data API)
- `web_search` - Google search results (SerpAPI)
- `website_reader` - Read and extract website content (BeautifulSoup)

**Tool Configuration:**
Tools are defined in `backend/api_agents/agent_tools_config.py` with OpenAI function definitions.

### 5. Credit System

**Allocation:**
- New users: 100 credits
- Monthly refresh: 100 credits on the 1st
- Auto-refresh enabled

**Credit Costs:**
- Chat message: 1 credit
- Tool call: 2 credits
- Admin can add credits

**Usage Tracking:**
All actions logged in `UsageLog` model.

### 6. Workflow Automation

**Visual Workflow Builder:**
- React Flow integration
- Drag-and-drop nodes
- Connect nodes with edges
- Save workflow structure as JSON

**Trigger Types:**

**Scheduled (Cron):**
```json
{
  "type": "scheduled",
  "schedule": "0 9 * * *",  // Every day at 9 AM
  "command": "Send daily summary"
}
```

**Event-Based (App Events):**
```json
{
  "type": "app_event",
  "trigger_id": "gmail_new_email",
  "command": "Process incoming email"
}
```

**Manual:**
```json
{
  "type": "manual",
  "command": "Generate report"
}
```

### 7. Telegram Bot Integration

**Setup:**
1. Create Telegram bot via @BotFather
2. Connect agent to bot in UI
3. Backend configures webhook
4. Users message bot → Agent responds

**Features:**
- Bidirectional messaging
- Session management
- Multi-user support

### 8. Social OAuth Authentication

**Google OAuth:**
- Sign up/in with Google account
- Uses `@react-oauth/google` on frontend
- django-allauth on backend

**GitHub OAuth:**
- Sign up/in with GitHub account
- OAuth callback handling
- User profile creation

---

## Development Workflow

### Making Changes

#### 1. Backend Changes

```bash
# Create feature branch
git checkout -b feature/new-endpoint

# Make changes to backend code
cd backend
# Edit files in api_agents/

# Test locally
python manage.py runserver

# Create migrations if models changed
python manage.py makemigrations

# Test migrations
python manage.py migrate

# Commit changes
git add .
git commit -m "Add new endpoint for X"

# Push to remote
git push origin feature/new-endpoint

# Deploy to EC2
cd ..
./deploy-to-ec2.sh
```

#### 2. Frontend Changes

```bash
# Create feature branch
git checkout -b feature/new-ui-component

# Make changes to frontend code
cd frontend
# Edit files in src/

# Test locally
npm run dev

# Build for production
npm run build:prod

# Commit changes
git add .
git commit -m "Add new UI component for X"

# Push to remote
git push origin feature/new-ui-component

# Deploy to EC2
cd ..
./deploy-to-ec2.sh
```

#### 3. Adding New Dependencies

**Backend:**
```bash
cd backend
pip install new-package
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Add new-package dependency"

# Deploy (will rebuild Docker image)
cd ..
./deploy-to-ec2.sh
```

**Frontend:**
```bash
cd frontend
npm install new-package
git add package.json package-lock.json
git commit -m "Add new-package dependency"

# Deploy
cd ..
./deploy-to-ec2.sh
```

### Testing

**Backend Tests:**
```bash
cd backend
python manage.py test

# Run specific test
python manage.py test api_agents.tests.test_agents

# With coverage
pip install coverage
coverage run manage.py test
coverage report
```

**Frontend Tests:**
```bash
cd frontend
npm run test  # If configured
npm run lint  # ESLint
```

### Code Style

**Backend (Python):**
- Follow PEP 8 style guide
- Use Django conventions
- Type hints recommended

**Frontend (TypeScript):**
- Use ESLint configuration
- TypeScript strict mode
- React best practices

---

## Troubleshooting

### Common Issues and Solutions

#### 1. CORS Errors

**Problem:** Frontend can't connect to backend

**Solution:**
```bash
# Edit backend/.env
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://13.62.63.125

# Restart backend
sudo docker compose restart backend
```

#### 2. Database Connection Failed

**Problem:** Backend can't connect to PostgreSQL

**Solution:**
```bash
# Check DATABASE_URL in backend/.env
# Format: postgresql://user:password@host:5432/database

# Test connection
ssh -i ~/Downloads/kgen.pem ubuntu@13.62.63.125
sudo docker compose exec backend python manage.py dbshell
```

#### 3. Static Files Not Loading

**Problem:** CSS/JS not loading in production

**Solution:**
```bash
# Rebuild frontend
cd frontend
npm run build:prod

# Collect static files
ssh -i ~/Downloads/kgen.pem ubuntu@13.62.63.125
cd /home/ubuntu/KGen21
sudo docker compose exec backend python manage.py collectstatic --noinput

# Restart nginx
sudo docker compose restart nginx
```

#### 4. OAuth Not Working

**Problem:** Google/GitHub login fails

**Solution:**
```bash
# Check credentials in backend/.env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...

# Verify redirect URIs in OAuth app settings:
# Google: http://13.62.63.125/api/auth/google/callback/
# GitHub: http://13.62.63.125/api/auth/github/callback/

# Restart backend
sudo docker compose restart backend
```

#### 5. Docker Container Won't Start

**Problem:** Container exits immediately

**Solution:**
```bash
# Check logs
sudo docker compose logs backend
sudo docker compose logs nginx

# Common issues:
# - Missing .env file
# - Incorrect environment variables
# - Port already in use

# Restart with fresh build
sudo docker compose down
sudo docker compose up -d --build
```

#### 6. Nginx 502 Bad Gateway

**Problem:** Nginx can't reach backend

**Solution:**
```bash
# Check backend is running
sudo docker compose ps

# Check backend health
sudo docker compose exec backend curl http://localhost:8000/api/

# Check nginx config
sudo docker compose exec nginx nginx -t

# Wait longer (backend might be starting)
sleep 30

# Check logs
sudo docker compose logs backend
sudo docker compose logs nginx
```

#### 7. Streaming Chat Not Working

**Problem:** SSE events not received

**Solution:**
```bash
# Check nginx config for SSE support
# Ensure proxy_buffering off for /api/agents/*/chat/

# Check CORS headers
# Ensure EventSource can connect

# Test SSE endpoint
curl -N http://13.62.63.125/api/agents/{id}/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

#### 8. Missing API Keys

**Problem:** Tool calls fail

**Solution:**
```bash
# Edit backend/.env with all required keys
OPENAI_API_KEY=sk-...
COMPOSIO_API_KEY=...
YOUTUBE_API_KEY=...
SERPAPI_KEY=...

# Restart backend
sudo docker compose restart backend

# Verify in logs
sudo docker compose logs backend | grep -i "api key"
```

### Log Locations

**Docker Logs:**
```bash
# All services
sudo docker compose logs -f

# Specific service
sudo docker compose logs -f backend
sudo docker compose logs -f nginx

# Last N lines
sudo docker compose logs --tail=100

# Follow with timestamps
sudo docker compose logs -f --timestamps
```

**Django Logs:**
```bash
# Inside container
sudo docker compose exec backend bash
cat /var/log/gunicorn.log  # If configured

# stdout/stderr
sudo docker compose logs backend
```

**Nginx Logs:**
```bash
# Inside container
sudo docker compose exec nginx bash
cat /var/log/nginx/access.log
cat /var/log/nginx/error.log

# Or via docker logs
sudo docker compose logs nginx
```

---

## Useful Commands

### Docker Commands

```bash
# View all containers
sudo docker ps -a

# View images
sudo docker images

# Stop all containers
sudo docker stop $(sudo docker ps -q)

# Remove all containers
sudo docker rm $(sudo docker ps -a -q)

# Remove all images
sudo docker rmi $(sudo docker images -q)

# Clean up system
sudo docker system prune -a

# View container resource usage
sudo docker stats

# Copy files from container
sudo docker cp kgen_backend:/app/db.sqlite3 ./backup.sqlite3

# Copy files to container
sudo docker cp ./file.txt kgen_backend:/app/

# Execute command in container
sudo docker compose exec backend ls -la

# View container logs
sudo docker logs kgen_backend
```

### Django Management Commands

```bash
# Inside container
sudo docker compose exec backend python manage.py [command]

# Common commands:
migrate                    # Run migrations
makemigrations             # Create migrations
createsuperuser           # Create admin user
shell                     # Django shell
dbshell                   # Database shell
collectstatic             # Collect static files
seed_agent_templates      # Seed templates
sync_composio_apps        # Sync Composio apps
runserver                 # Development server (don't use in production)
test                      # Run tests
showmigrations            # Show migration status
flush                     # Clear database
dumpdata                  # Export data
loaddata                  # Import data
```

### SSH and SCP Commands

```bash
# SSH to EC2
ssh -i ~/Downloads/kgen.pem ubuntu@13.62.63.125

# Copy file to EC2
scp -i ~/Downloads/kgen.pem file.txt ubuntu@13.62.63.125:/home/ubuntu/

# Copy directory to EC2
scp -i ~/Downloads/kgen.pem -r ./directory ubuntu@13.62.63.125:/home/ubuntu/

# Copy file from EC2
scp -i ~/Downloads/kgen.pem ubuntu@13.62.63.125:/home/ubuntu/file.txt ./

# Run command on EC2 without SSH session
ssh -i ~/Downloads/kgen.pem ubuntu@13.62.63.125 "cd KGen21 && sudo docker compose ps"
```

### Git Commands

```bash
# Clone repository
git clone <repo-url>

# Create branch
git checkout -b feature/new-feature

# Stage changes
git add .

# Commit
git commit -m "Description"

# Push
git push origin feature/new-feature

# Pull latest
git pull origin main

# View status
git status

# View logs
git log --oneline

# Stash changes
git stash
git stash pop
```

### Node/NPM Commands

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build:prod

# Preview production build
npm run preview

# Lint code
npm run lint

# Update dependencies
npm update

# Check outdated packages
npm outdated

# Clear cache
npm cache clean --force
```

---

## Security

### Environment Variables

- **Never commit `.env` files** to version control
- Use `.env.example` as template
- Store production secrets securely (AWS Secrets Manager, etc.)
- Rotate API keys regularly

### Django Security Settings

```python
# Production settings (backend/config/settings.py)

DEBUG = False  # Must be False in production
ALLOWED_HOSTS = ['13.62.63.125', 'yourdomain.com']
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')  # Strong, random key

# HTTPS settings (when SSL configured)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### CORS Configuration

```python
# Only allow specific origins
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Development
    "http://13.62.63.125",    # Production
]

# Don't use CORS_ALLOW_ALL_ORIGINS = True in production
```

### Authentication Best Practices

- JWT tokens stored in HttpOnly cookies (prevents XSS)
- CSRF protection enabled
- Password validators enforced
- Email verification required
- Rate limiting on auth endpoints (consider django-ratelimit)

### File Upload Security

- Validate file types and sizes
- Scan uploads for malware (consider ClamAV)
- Store files with random names
- Limit upload size in nginx config

### Docker Security

- Run containers as non-root user (already configured)
- Keep base images updated
- Scan images for vulnerabilities
- Use multi-stage builds (already configured)
- Don't expose unnecessary ports

### SSL/HTTPS Setup

**Using Let's Encrypt:**

```bash
# Install Certbot
ssh -i ~/Downloads/kgen.pem ubuntu@13.62.63.125
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (already set up by certbot)
sudo certbot renew --dry-run
```

### Database Security

- Use strong passwords
- Enable SSL for database connections
- Regular backups
- Restrict database access to backend only
- Use environment variables for credentials

### Security Checklist

- [ ] DEBUG = False in production
- [ ] Strong SECRET_KEY
- [ ] ALLOWED_HOSTS configured
- [ ] CORS_ALLOWED_ORIGINS configured
- [ ] HTTPS enabled (SSL certificate)
- [ ] HttpOnly cookies for JWT
- [ ] CSRF protection enabled
- [ ] Email verification required
- [ ] Strong password validation
- [ ] Regular security updates
- [ ] Database backups automated
- [ ] API keys rotated periodically
- [ ] Firewall configured (AWS Security Groups)
- [ ] SSH key-based auth only
- [ ] Regular log monitoring

---

## Contributing

We welcome contributions! Please follow these guidelines:

### Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Test thoroughly
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Code Standards

**Backend (Python):**
- Follow PEP 8
- Write docstrings for functions/classes
- Add type hints
- Write tests for new features
- Update API documentation

**Frontend (TypeScript):**
- Follow ESLint rules
- Use TypeScript strict mode
- Write meaningful component names
- Add comments for complex logic
- Test UI components

### Commit Messages

Use conventional commits:
```
feat: add new agent tool
fix: resolve CORS issue
docs: update README
refactor: simplify auth logic
test: add unit tests for agents
```

### Pull Request Process

1. Update README if needed
2. Add tests for new features
3. Ensure all tests pass
4. Update CHANGELOG
5. Request review from maintainers

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

For issues, questions, or suggestions:

- **Issues**: [GitHub Issues](https://github.com/yourusername/KGen21/issues)
- **Email**: support@yourdomain.com
- **Documentation**: [API Docs](http://13.62.63.125/api/docs/)

---

## Acknowledgments

- **OpenAI** - AI capabilities
- **Composio** - Tool integrations
- **Django** - Backend framework
- **React** - Frontend framework
- **shadcn/ui** - UI components
- **TanStack Query** - Data fetching
- **Vite** - Build tool
- **Docker** - Containerization

---

<div align="center">

**Built with ❤️ for AI Agent Automation**

[Back to Top](#kgen21---ai-agent-creator-platform)

</div>
