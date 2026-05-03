# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Spec-first repository

The authoritative description of this project lives in `docs/`. Read these before writing code:

- `docs/vision.md` — actors and problem statement (10-room hotel; Guest, Receptionist, Manager, Housekeeping).
- `docs/requirements.md` — functional requirements catalog FR-001…FR-010.
- `docs/architecture.md` — stack, repo layout, local dev setup, backend/frontend structure, and the list of decisions deliberately deferred (entity model, DynamoDB physical design, identifier strategy, auth, use case specs).

The current state is a scaffold only — no domain logic. The split `backend/app/{api,models,repositories,services}/` is empty by design until the entity model and use case specs land. Do not invent entities, table designs, or auth schemes ahead of those docs.

## Commands

### Backend (`backend/`, Python 3.13, uv)
```bash
uv sync                                         # install from uv.lock
uv run uvicorn app.main:app --reload            # run API locally
uv run pytest                                   # run all tests
uv run pytest tests/test_smoke.py::test_health  # single test
uv run ruff check . && uv run ruff format --check .
uv run pyright
```

### Frontend (`frontend/`, Angular 21, npm)
```bash
npm install
npm start          # ng serve
npm run build
npm test           # vitest (jsdom)
```

### Infra
```bash
docker compose -f infra/docker-compose.yml up -d   # DynamoDB Local on :8000
cd infra/cdk && uv run pytest                      # CDK synth tests
cd infra/cdk && uv run cdk synth                   # synthesize CloudFormation
```

For local backend dev against DynamoDB Local, set `DYNAMODB_ENDPOINT_URL=http://localhost:8000` plus dummy AWS credentials (see `docs/architecture.md` §3).

## Architecture notes that span files

- **Lambda packaging**: `backend/Dockerfile` builds the image; `infra/cdk/stacks/hrs_stack.py` consumes it via `DockerImageCode.from_image_asset(BACKEND_ROOT)` and exposes it through API Gateway. `backend/app/lambda_handler.py` is the entry point (`Mangum(app)`).
- **Dual-mode DynamoDB**: prod gets the table from CDK; dev creates it idempotently in the FastAPI `lifespan` against DynamoDB Local. The lifespan must short-circuit when `DYNAMODB_ENDPOINT_URL` is unset.
- **OpenAPI contract**: the Angular client is intended to be generated from FastAPI's OpenAPI schema (`ng-openapi-gen` / `openapi-generator-cli`) — keep request/response DTOs in `backend/app/models/` typed precisely so the generated client stays useful.
- **Tooling lives in `pyproject.toml`**: ruff, pyright, and pytest config are not in separate files. `.pre-commit-config.yaml` runs ruff on `backend/` and `infra/cdk/` only.

## Local divergence to be aware of

`infra/cdk/stacks/hrs_stack.py` and its synth test currently have the DynamoDB table removed (uncommitted change on `main`). The architecture doc still describes the table as part of the CDK stack — treat the doc as the target state and confirm with the user before re-adding or further removing infra resources.
