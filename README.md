# Dobble – Smart Doctor Appointment & Reporting Assistant

A full-stack **agentic AI** app for doctor appointments and reports. Patients book appointments in plain language; doctors get summary reports. The LLM agent uses **MCP (Model Context Protocol)** to discover and call tools (list doctors, check availability, book, send reports to Slack).

---

## Table of contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment setup](#environment-setup)
- [How to put .env files](#how-to-put-env-files)
- [Running the app](#running-the-app)
- [Full working tutorial](#full-working-tutorial)
- [How to use (by role)](#how-to-use-by-role)
- [Optional: Calendar, Email, Slack](#optional-calendar-email-slack)
- [Troubleshooting](#troubleshooting)
- [Project layout](#project-layout)
- [API reference](#api-reference)
- [Environment variables (full list)](#environment-variables-full-list)

---

## Architecture

| Layer     | Technology |
|----------|------------|
| Frontend | Next.js (auth, dashboard, Assistant chat) |
| Backend  | FastAPI + MCP server |
| Database | PostgreSQL (Prisma Python: doctors, patients, appointments, availability) |
| LLM     | Gemini (tool-calling via MCP) |
| Calendar | Google Calendar API (optional) |
| Email    | SendGrid (optional) |
| Notify   | Slack (optional, for doctor reports) |

**Flow:** Sign in as **Patient** or **Doctor** → **Dashboard** → **Assistant** → chat is sent to FastAPI → Gemini agent calls MCP tools (list doctors, book, stats, send report) → reply and actions (DB, Calendar, email, Slack) happen automatically.

---

## Prerequisites

- **Node.js** 18+ and **npm**
- **Python** 3.10+
- **PostgreSQL** (local or hosted)
- **Google Cloud project** with Vertex AI enabled, and auth: `gcloud auth application-default login`

---

## Installation

### 1. Clone and enter the project

```bash
git clone <repo-url>
cd Dobble
```

### 2. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Database and Prisma

- Create a PostgreSQL database (e.g. `dobble`).
- Create **`backend/.env`** from the example: `cp backend/env.example backend/.env`, then fill in `DATABASE_URL`, `JWT_SECRET`, `VERTEXAI_PROJECT`, and `VERTEXAI_LOCATION` (see [How to put .env files](#how-to-put-env-files)).

Then:

```bash
cd backend
./db_push.sh                       # Push schema to DB (uses backend/.env only)
bash generate_prisma.sh            # Generate Prisma Python client
PYTHONPATH=. .venv/bin/python seed_db.py   # Seed sample doctors and a patient
```

**Seeded users (for testing):**

- **Doctors:** Dr. Ahuja (`ahuja@clinic.com`), Dr. Smith (`smith@clinic.com`), Dr. Lee (`lee@clinic.com`) — password: `password123`
- **Patient:** `patient@example.com` — password: `password123`

### 4. Frontend setup

From the **project root** (not inside `backend`):

```bash
npm install
```

Create **root `.env`** from the example: `cp env.example .env`, then fill in the values (see [How to put .env files](#how-to-put-env-files)).

---

## Environment setup

Dobble uses **two** `.env` files. Example files are provided so you can copy and fill in values.

| File | Location | Purpose |
|------|----------|---------|
| **Root `.env`** | Project root (same folder as `package.json`) | Next.js, NextAuth, backend URL |
| **Backend `.env`** | Inside `backend/` | FastAPI, DB, Gemini, optional Calendar/Email/Slack |

**Minimal required variables:**

- **Root:** `NEXTAUTH_URL`, `NEXTAUTH_SECRET`, `DATABASE_URL` (and optionally `BACKEND_URL`).
- **Backend:** `DATABASE_URL`, `JWT_SECRET`, `VERTEXAI_PROJECT`, `VERTEXAI_LOCATION`.

Optional variables (Calendar, SendGrid, Slack) are described in [Optional: Calendar, Email, Slack](#optional-calendar-email-slack). A [full list of environment variables](#environment-variables-full-list) is at the end of this README.

---

## How to put .env files

### 1. Root `.env` (for Next.js)

From the **project root** (where `package.json` is):

```bash
cp env.example .env
```

Then open `.env` and replace placeholders:

| Variable | What to put |
|----------|-------------|
| `NEXTAUTH_URL` | `http://localhost:3000` (or your frontend URL) |
| `NEXTAUTH_SECRET` | Output of `openssl rand -base64 32` (run in terminal, paste the line) |
| `DATABASE_URL` | Your PostgreSQL URL, e.g. `postgresql://myuser:mypass@localhost:5432/dobble` |
| `BACKEND_URL` | `http://localhost:8000` (or your backend URL) |

**Example root `.env` after editing:**

```env
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=K7x9mN2pQ5rT8vY1zA3bC6dE0fG2hJ4kL
DATABASE_URL=postgresql://myuser:mypass@localhost:5432/dobble
BACKEND_URL=http://localhost:8000
```

(Use your own secret and DB credentials; do not commit `.env` to git.)

---

### 2. Backend `.env` (for FastAPI)

From the **project root**:

```bash
cp backend/env.example backend/.env
```

Or from inside `backend/`:

```bash
cd backend
cp env.example .env
```

Then open `backend/.env` and replace placeholders:

| Variable | What to put |
|----------|-------------|
| `DATABASE_URL` | Same PostgreSQL URL as in root `.env` |
| `JWT_SECRET` | Output of `openssl rand -base64 32` (can be same or different from NEXTAUTH_SECRET) |
| `VERTEXAI_PROJECT` | Your GCP project ID (Vertex AI must be enabled) |
| `VERTEXAI_LOCATION` | Region, e.g. `us-central1` |

**Example backend `.env` (minimal, required only):**

```env
DATABASE_URL=postgresql://myuser:mypass@localhost:5432/dobble
JWT_SECRET=K7x9mN2pQ5rT8vY1zA3bC6dE0fG2hJ4kL
VERTEXAI_PROJECT=my-gcp-project-id
VERTEXAI_LOCATION=us-central1
```

**Example backend `.env` (with optional Calendar, SendGrid, Slack):**

```env
DATABASE_URL=postgresql://myuser:mypass@localhost:5432/dobble
JWT_SECRET=your-jwt-secret
VERTEXAI_PROJECT=my-gcp-project-id
VERTEXAI_LOCATION=us-central1

# Google Calendar (OAuth)
GOOGLE_OAUTH_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=xxx
GOOGLE_OAUTH_REFRESH_TOKEN=1//xxx
GOOGLE_CALENDAR_ID=primary

# SendGrid
SENDGRID_API_KEY=SG.xxx
SENDGRID_FROM_EMAIL=noreply@yourdomain.com

# Slack
SLACK_BOT_TOKEN=xoxb-xxx
SLACK_CHANNEL_ID=C01234ABCD

FRONTEND_ORIGIN=http://localhost:3000
```

- **No spaces** before variable names (e.g. `SLACK_BOT_TOKEN=...`, not `   SLACK_BOT_TOKEN=...`).
- **No quotes** around values unless the value itself contains spaces.
- Do not commit `backend/.env` to git.

---

### Quick checklist

- [ ] Root: `cp env.example .env` → set `NEXTAUTH_URL`, `NEXTAUTH_SECRET`, `DATABASE_URL`, `BACKEND_URL`
- [ ] Backend: `cp backend/env.example backend/.env` → set `DATABASE_URL`, `JWT_SECRET`, `VERTEXAI_PROJECT`, `VERTEXAI_LOCATION`
- [ ] Optional: add Google/SendGrid/Slack vars to `backend/.env` as needed (see [Optional: Calendar, Email, Slack](#optional-calendar-email-slack))

---

## Running the app

Use **two terminals**.

**Terminal 1 – Backend**

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. python run.py
```

- Backend: **http://localhost:8000**
- Health: **http://localhost:8000/health**

**Terminal 2 – Frontend**

```bash
npm run dev
```

- Frontend: **http://localhost:3000**

Open **http://localhost:3000** in your browser.

---

## Full working tutorial

### Step 1: Sign up or log in

1. Go to **http://localhost:3000**.
2. Click **Sign up** (or **Log in** if you already have an account).
3. **Sign up:** Choose **Patient** or **Doctor**, enter name, email, password → submit. You’ll be logged in.
4. **Log in:** Use a seeded account (e.g. `patient@example.com` / `password123` as Patient, or `ahuja@clinic.com` / `password123` as Doctor).

### Step 2: Use the Assistant as a Patient

1. In the nav, click **Assistant**.
2. You’ll see the **Patient** view (booking).
3. Try:
   - **"What doctors are available?"** → The agent lists doctors (e.g. Dr. Ahuja, Dr. Smith, Dr. Lee).
   - **"I want to check Dr. Ahuja's availability for tomorrow."** → The agent returns free slots.
   - **"Book the 2 PM slot for tomorrow. My name is John, email john@example.com."** → The agent books the appointment (DB + optional Calendar + email). Your **logged-in** email is used if you’re signed in; otherwise the agent may ask for name/email.
4. Open **Appointments** in the nav to see your bookings.
5. Ask **"What are my upcoming appointments?"** → The agent lists your appointments (uses your logged-in email).

### Step 3: Use the Assistant as a Doctor

1. Sign out and sign in as a **Doctor** (e.g. `ahuja@clinic.com` / `password123`), or use an account you created as Doctor.
2. Click **Assistant**.
3. You’ll see the **Doctor** view (reports).
4. Try:
   - **"How many patients do I have today?"**
   - **"How many patients visited yesterday?"**
   - **"Give me a summary of today's appointments."**
5. The agent fetches stats and sends a report. If Slack is configured, the report is also posted to your Slack channel (#dobble-reports); otherwise you see the summary in the chat.

### Step 4: Appointments and Profile

- **Appointments:** View and manage your appointments (cancel if allowed).
- **Profile:** View (and edit, if implemented) your profile.

---

## How to use (by role)

### As a Patient

- **Assistant:** Book in plain language. Examples:
  - *"What doctors are available?"*
  - *"Check Dr. Ahuja's availability for Friday afternoon."*
  - *"Book the 3 PM slot for Friday. My name is Jane, email jane@example.com."*
  - *"What are my upcoming appointments?"*
- **Appointments:** See and cancel your appointments.
- **Profile:** See your details.

### As a Doctor

- **Assistant:** Ask for stats and reports. Examples:
  - *"How many patients visited yesterday?"*
  - *"How many appointments do I have today and tomorrow?"*
  - *"How many patients with fever?"*
  - *"Give me a summary report."*
- Reports are shown in the chat and, when configured, posted to Slack (#dobble-reports).
- **Appointments:** See your schedule.
- **Profile:** See your details.

---

## Optional: Calendar, Email, Slack

Without these, the app still works: bookings go to the DB; email and Slack are stubbed (logged only).

### Google Calendar

- **Option A – Service account:** Set `GOOGLE_CREDENTIALS_FILE=path/to/service-account.json` and optionally `GOOGLE_CALENDAR_ID=primary` in `backend/.env`.
- **Option B – OAuth (e.g. when org blocks service accounts):** Create an OAuth 2.0 Client ID in Google Cloud Console, then:
  ```bash
  cd backend
  GOOGLE_OAUTH_CLIENT_ID=xxx GOOGLE_OAUTH_CLIENT_SECRET=xxx python scripts/get_google_refresh_token.py
  ```
  Add the printed refresh token and client id/secret to `backend/.env`. Set `GOOGLE_CALENDAR_ID=primary` (or your calendar ID).

### SendGrid (email)

- Sign up at [SendGrid](https://sendgrid.com), create an API key, and verify a sender.
- In `backend/.env`: `SENDGRID_API_KEY=SG.xxx`, `SENDGRID_FROM_EMAIL=noreply@yourdomain.com`.

### Slack (doctor reports)

1. Create an app at [api.slack.com/apps](https://api.slack.com/apps) (e.g. “Dobble”).
2. **OAuth & Permissions** → **Bot Token Scopes** → add **`chat:write`**.
3. **Manage Distribution** → **Add to Slack** (or use the Sharable URL) → choose workspace → **Allow**.
4. Copy the **Bot User OAuth Token** (`xoxb-...` or `xoxe.xoxb-...`) and put it in `backend/.env`:
   ```env
   SLACK_BOT_TOKEN=xoxb-...
   SLACK_CHANNEL_ID=C01234ABCD
   ```
   (Get channel ID: open the channel in Slack → click channel name → scroll to Channel ID.)
5. In Slack, in the channel you use (e.g. #dobble-reports), run: `/invite @Dobble`.
6. Restart the backend.

**If you get `missing_scope` / `chat:write:bot`:** Add **chat:write** under Bot Token Scopes, click **Manage Distribution** → **Add to Slack** (or open the Sharable URL), choose your workspace, click **Allow**. Then copy the **new** Bot User OAuth Token from **OAuth & Permissions** into `SLACK_BOT_TOKEN` in `backend/.env`, and restart the backend.

---

## Troubleshooting

- **"Conflict between env var in ../.env and .env"**  
  Use `./db_push.sh` from `backend/` so only `backend/.env` is used for Prisma.

- **Slack: `missing_scope`, `chat:write:bot`**  
  Add **chat:write** under Bot Token Scopes, then **Manage Distribution** → **Add to Slack** → choose workspace → **Allow**. Copy the new Bot User OAuth Token from **OAuth & Permissions** into `SLACK_BOT_TOKEN` in `backend/.env`, restart backend.

- **"You have no upcoming appointments" (Patient)**  
  Ensure you’re logged in with the same email used to book. Log out and log in again so the session has your email; then ask "What are my upcoming appointments?" again.

- **Backend: "Gemini not configured"**  
  Set `VERTEXAI_PROJECT` and `VERTEXAI_LOCATION` in `backend/.env`, run `gcloud auth application-default login`, and restart.

- **Frontend: "Please sign in"**  
  Set `NEXTAUTH_SECRET` and `NEXTAUTH_URL` in root `.env`; ensure the backend is running so login/register can succeed.

---

## Project layout

```
Dobble/
├── app/                    # Next.js app (auth, dashboard, Assistant)
│   ├── (auth)/login, signup
│   ├── api/                # Next.js API routes
│   └── dashboard/          # Dashboard, Appointments, Profile, Assistant
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI, /api/chat, /api/doctor-report, MCP
│   │   ├── agent.py        # LLM agent (Gemini + MCP)
│   │   ├── mcp_server.py   # MCP tools (FastMCP)
│   │   ├── tools_impl.py   # Tool implementations
│   │   ├── config.py, db.py, auth.py
│   │   └── services/        # calendar, email, notification
│   ├── prisma/schema.prisma
│   ├── seed_db.py, run.py
│   └── scripts/get_google_refresh_token.py
├── components/, lib/
├── env.example             # Copy to .env (root)
├── backend/env.example     # Copy to backend/.env
└── README.md
```

---

## API reference

| Method | Endpoint            | Description |
|--------|---------------------|-------------|
| GET    | /health             | Health check |
| POST   | /api/auth/register  | Register (patient/doctor) |
| POST   | /api/auth/login     | Login |
| GET    | /api/me             | Current user (JWT) |
| POST   | /api/chat           | Patient chat: `{ "prompt", "session_id?", "role": "patient", "patient_name?", "patient_email?" }` |
| POST   | /api/doctor-report  | Doctor report: `{ "prompt", "session_id?", "doctor_name?", "doctor_email?" }` |
| GET    | /api/appointments   | List appointments (JWT) |
| POST   | /api/appointments   | Create appointment (patient, JWT) |
| MCP    | /mcp                | MCP server (tools for the agent) |

Next.js rewrites `/api/agent/*` to the backend so the Assistant page uses these APIs.

---

## MCP tools (backend)

Used by the Gemini agent via MCP:

1. **list_doctors** – List all doctors (name, email, specialization).
2. **get_doctor_availability** – Get free slots for a doctor on a date.
3. **book_appointment** – Book (DB + optional Calendar + email).
4. **list_my_appointments** – List upcoming appointments for a patient (by email).
5. **send_email_confirmation** – Send email (e.g. confirmation).
6. **get_doctor_stats** – Stats (visits yesterday, appointments today/tomorrow, patients by condition).
7. **send_doctor_report** – Send report to Slack or in-app.

---

## Environment variables (full list)

### Root `.env` (project root)

| Variable | Required | Example | Purpose |
|----------|----------|---------|---------|
| **NEXTAUTH_URL** | Yes | `http://localhost:3000` | NextAuth app URL. |
| **NEXTAUTH_SECRET** | Yes | (output of `openssl rand -base64 32`) | Secret for NextAuth JWT. |
| **DATABASE_URL** | Yes | `postgresql://user:pass@localhost:5432/dobble` | PostgreSQL connection (same as backend). |
| **BACKEND_URL** | No | `http://localhost:8000` | FastAPI backend URL. |

### Backend `.env` (`backend/.env`)

**Required**

| Variable | Example | Purpose |
|----------|---------|---------|
| **DATABASE_URL** | `postgresql://user:pass@localhost:5432/dobble` | PostgreSQL for Prisma. |
| **JWT_SECRET** | (output of `openssl rand -base64 32`) | JWT signing secret. |
| **VERTEXAI_PROJECT** | `my-gcp-project-id` | GCP project (Vertex AI enabled). Auth: `gcloud auth application-default login` |
| **VERTEXAI_LOCATION** | `us-central1` | Vertex AI region. |

**Optional – Google Calendar**

| Variable | Example | Purpose |
|----------|---------|---------|
| **GOOGLE_CREDENTIALS_FILE** | `path/to/service-account.json` | Service account (option A). |
| **GOOGLE_OAUTH_CLIENT_ID** | `xxx.apps.googleusercontent.com` | OAuth client ID (option B). |
| **GOOGLE_OAUTH_CLIENT_SECRET** | (from GCP) | OAuth client secret. |
| **GOOGLE_OAUTH_REFRESH_TOKEN** | (from `scripts/get_google_refresh_token.py`) | OAuth refresh token. |
| **GOOGLE_CALENDAR_ID** | `primary` | Calendar to use (default `primary`). |

**Optional – SendGrid**

| Variable | Example | Purpose |
|----------|---------|---------|
| **SENDGRID_API_KEY** | `SG.xxx` | SendGrid API key. |
| **SENDGRID_FROM_EMAIL** | `noreply@yourdomain.com` | Sender (must be verified). |

**Optional – Slack**

| Variable | Example | Purpose |
|----------|---------|---------|
| **SLACK_BOT_TOKEN** | `xoxb-xxx` | Bot token (**chat:write** scope required). |
| **SLACK_CHANNEL_ID** | `C01234ABCD` | Channel ID for doctor reports. |

**Optional – other**

| Variable | Example | Purpose |
|----------|---------|---------|
| **FRONTEND_ORIGIN** | `http://localhost:3000` | CORS origin. |
| **MCP_SERVER_URL** | `http://localhost:8000/mcp/sse` | MCP SSE URL. |
| **JWT_EXPIRE_MINUTES** | `10080` | JWT lifetime (minutes). |
