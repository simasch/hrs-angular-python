# Hotel Reservation System (HRS)

A small reservation system for a ten-room hotel. The work is **spec-first**: the design lives in `docs/` (vision, requirements, architecture) and code is added against those specs.

If you are new to Angular or Python, this README is enough to get the project running on your machine. You do not need to understand the frameworks to run the steps below.

## What is in this repo

| Folder      | What it is                | Language / runtime   |
|-------------|---------------------------|----------------------|
| `docs/`     | The specification         | Markdown             |
| `backend/`  | The web API               | Python 3.13 + FastAPI |
| `frontend/` | The web UI                | Angular 21 (TypeScript) |
| `infra/`    | Local DB + AWS deployment | Docker + AWS CDK     |

The backend serves JSON over HTTP. The frontend is a single-page web app that calls the backend. They run as two separate processes during development.

## One-time prerequisites

Install these once. Versions in parentheses are what the project targets — newer is usually fine.

1. **Python 3.13** — used by the backend and the AWS CDK app.
2. **uv** — the Python package and virtual-environment manager used here. Think of it as "`npm` for Python". Install: <https://docs.astral.sh/uv/getting-started/installation/>.
3. **Node.js 20+ and npm** — needed to run the Angular frontend. Install: <https://nodejs.org/>.
4. **Docker Desktop** (or any Docker engine) — used to run a local DynamoDB database in a container. Install: <https://www.docker.com/products/docker-desktop/>.

You do **not** need an AWS account to develop locally.

Quick check that everything is installed:

```bash
python3 --version    # 3.13.x
uv --version
node --version       # v20.x or higher
npm --version
docker --version
```

## First-time setup

Run these from the repository root.

### 1. Start the local database

DynamoDB is the database. We run a free local copy of it inside Docker.

```bash
docker compose -f infra/docker-compose.yml up -d
```

This downloads the database image the first time and runs it in the background on `http://localhost:8000`. To stop it later: `docker compose -f infra/docker-compose.yml down`.

### 2. Install backend dependencies

```bash
cd backend
uv sync
```

`uv sync` reads `uv.lock` and creates a virtual environment in `backend/.venv` with all required Python packages.

### 3. Install frontend dependencies

```bash
cd frontend
npm install
```

This downloads the Angular packages into `frontend/node_modules`.

## Running the app

You need two terminals: one for the backend, one for the frontend. The Docker database from setup step 1 must also be running.

### Terminal 1 — backend (the API)

```bash
cd backend
DYNAMODB_ENDPOINT_URL=http://localhost:8000 \
AWS_ACCESS_KEY_ID=dummy \
AWS_SECRET_ACCESS_KEY=dummy \
AWS_REGION=eu-central-1 \
uv run uvicorn app.main:app --reload
```

The API is now running on <http://localhost:8000>. Wait — that is the same port as DynamoDB Local. The default uvicorn port is `8000`, so add `--port 8001` if it clashes:

```bash
uv run uvicorn app.main:app --reload --port 8001
```

You should see `{"status":"ok"}` at <http://localhost:8001/health>. The interactive API docs are at <http://localhost:8001/docs>.

The dummy AWS variables are required because the AWS SDK refuses to talk to anything (even the local DB) without credentials. They are not real keys.

### Terminal 2 — frontend (the UI)

```bash
cd frontend
npm start
```

Open <http://localhost:4200> in your browser. The page reloads automatically when you edit a file in `frontend/src/`.

## Running the tests

```bash
# Backend
cd backend
uv run pytest

# Frontend
cd frontend
npm test

# Infrastructure (CDK synthesis)
cd infra/cdk
uv sync
uv run pytest
```

## Code quality (backend only)

```bash
cd backend
uv run ruff check .          # lint
uv run ruff format --check . # formatting
uv run pyright               # type check
```

Ruff is the Python linter and formatter; Pyright is the type checker. They are configured in `backend/pyproject.toml` — no separate config files.

## Where to read next

- `docs/vision.md` — what we are building and for whom.
- `docs/requirements.md` — the list of features (FR-001…FR-010).
- `docs/architecture.md` — the technology choices and why.
- `CLAUDE.md` — guidance for the Claude Code assistant working in this repo.

## Common problems

- **`docker compose` says "command not found"** — older Docker installs use `docker-compose` (with a hyphen). Same flags.
- **Port 8000 already in use** — run `docker compose -f infra/docker-compose.yml down` (DynamoDB Local) or use a different `--port` for uvicorn.
- **`uv: command not found` after install** — open a new terminal so the updated `PATH` is picked up.
- **Frontend shows nothing useful** — that is expected. The UI is a fresh Angular scaffold; real screens are added once the use cases in `docs/` are specified.
