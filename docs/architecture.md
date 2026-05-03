# Architecture

This document records the technology stack, repository layout, and local
development setup for the Hotel Reservation System (HRS).

It is a sibling of `vision.md` and `requirements.md`. At this stage only the
vision (actors, problem statement) and the functional requirements catalog
(FR-001…FR-010) are defined. Everything below is deliberately limited to
choices that follow from those two inputs. The physical data model, per-entity
module layout, and per-use-case access patterns are deferred until the entity
model and use case specifications are written.

## 1. Stack overview

| Layer         | Technology                          | Rationale                                                                 |
|---------------|-------------------------------------|---------------------------------------------------------------------------|
| Frontend      | Angular (latest LTS, standalone components) | Single-page app for guests, receptionists, housekeeping, and manager UIs (the four actors in `vision.md`). |
| Backend       | Python 3.13 + FastAPI + Pydantic v2  | Async, typed, auto-generates OpenAPI for the Angular client.              |
| Database      | Amazon DynamoDB                      | Fully managed, predictable per-request cost, fits the small but write-heavy reservation workload of a 10-room hotel. |
| Email         | Amazon SES (deferred)                | Used for booking confirmations (FR-003) and arrival reminders (FR-009). Stubbed locally. |
| AWS SDK       | `boto3` (sync)                       | Official Python SDK; `endpoint_url` override enables DynamoDB Local in dev. Sync handlers run on FastAPI's threadpool. |
| Tooling       | `uv`, `ruff`, `pyright`, `pytest`    | uv for dependency + venv management, ruff for lint + format, pyright for type checking, pytest (+ `pytest-asyncio`, `httpx`) for tests. |
| Test doubles  | `moto` + DynamoDB Local              | `moto` for fast in-process unit tests; DynamoDB Local for integration tests that exercise real query/transaction semantics. |
| Deployment    | AWS Lambda + API Gateway via `Mangum` | Mangum adapts the FastAPI ASGI app to API Gateway events. Pay-per-request matches the spiky 10-room workload and DynamoDB's pricing. |
| Observability | AWS Lambda Powertools for Python    | Structured JSON logging, X-Ray tracing, EMF metrics, idempotency helpers. The standard for Python on Lambda. |
| IaC           | AWS CDK (Python)                     | Models the Lambda function, API Gateway, and the DynamoDB table in the same language as the backend. |

## 2. Repository layout

```
hrs-angular-python/
├── docs/                  # Spec docs (vision, requirements, this file; entity model and use cases to follow)
├── frontend/              # Angular workspace (to be scaffolded)
├── backend/               # Python project (to be scaffolded)
│   ├── pyproject.toml     # Project metadata, dependencies, ruff/pyright/pytest config
│   ├── uv.lock            # Locked dependency graph, committed
│   ├── .python-version    # Pins Python 3.13 for uv
│   ├── app/               # Application code (see §4)
│   └── tests/             # pytest suite (unit with moto, integration with DynamoDB Local)
└── infra/
    ├── docker-compose.yml # Local DynamoDB
    └── cdk/               # AWS CDK app: Lambda + API Gateway + DynamoDB table
```

## 3. Local development

### DynamoDB Local via Docker

DynamoDB Local is the official AWS offering for offline development. We run it
via Docker Compose so the team and CI use the same image.

`infra/docker-compose.yml` (sketch):

```yaml
services:
  dynamodb:
    image: amazon/dynamodb-local:latest
    container_name: hrs-dynamodb-local
    command: ["-jar", "DynamoDBLocal.jar", "-sharedDb", "-dbPath", "/home/dynamodblocal/data"]
    ports:
      - "8000:8000"
    volumes:
      - dynamodb-data:/home/dynamodblocal/data
    working_dir: /home/dynamodblocal

volumes:
  dynamodb-data:
```

Notes:

- `-sharedDb` makes the tables visible regardless of AWS credentials/region —
  required for local dev across multiple tools.
- `-dbPath` plus the named volume preserves data across container restarts.
  Without it, every `docker compose down` wipes the database.
- Exposes `http://localhost:8000`.

### Backend wiring

The backend reads `DYNAMODB_ENDPOINT_URL` from the environment:

- **Dev:** `DYNAMODB_ENDPOINT_URL=http://localhost:8000`, dummy AWS
  credentials (e.g. `AWS_ACCESS_KEY_ID=dummy`, `AWS_SECRET_ACCESS_KEY=dummy`,
  `AWS_REGION=eu-central-1`).
- **Prod:** unset, so `boto3` resolves credentials and endpoint from the
  normal AWS chain.

```python
import boto3
from app.config import settings

def dynamodb_resource():
    kwargs = {"region_name": settings.aws_region}
    if settings.dynamodb_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamodb_endpoint_url
    return boto3.resource("dynamodb", **kwargs)
```

### Backend tooling

`uv` is the entry point for everything Python in `backend/`:

```bash
uv sync                       # create .venv + install from uv.lock
uv run uvicorn app.main:app --reload
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run pyright
```

`pyproject.toml` holds the ruff and pyright configuration alongside the dependency list — no separate config files. A `.pre-commit-config.yaml` runs ruff and pyright on staged files.

Dependencies (initial set):

- Runtime: `fastapi`, `pydantic`, `pydantic-settings`, `boto3`, `mangum`, `aws-lambda-powertools`.
- Dev: `pytest`, `pytest-asyncio`, `httpx`, `moto[dynamodb]`, `ruff`, `pyright`, `pre-commit`.

### GUI for browsing

[NoSQL Workbench](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/workbench.html)
is free and connects to DynamoDB Local — recommended for inspecting items
during development.

### Table creation

In dev the schema is created idempotently on backend startup (FastAPI
`lifespan`) against DynamoDB Local. In prod the same table is provisioned by
the CDK app in `infra/cdk/` — startup never touches the schema, so the
lifespan short-circuits when `DYNAMODB_ENDPOINT_URL` is unset.

The concrete table definition (keys, GSIs, item shapes) is deferred to the
data-modelling phase.

## 4. Backend structure (FastAPI)

```
backend/
└── app/
    ├── main.py              # FastAPI() instance, routers, lifespan (dev-only table creation)
    ├── lambda_handler.py    # `handler = Mangum(app)` — Lambda entry point
    ├── observability.py     # Powertools Logger, Tracer, Metrics singletons
    ├── config.py            # pydantic-settings: endpoint URL, table name, AWS region
    ├── api/                 # Route modules (one per use-case area, named once use cases are specified)
    ├── models/              # Pydantic request/response DTOs and persisted item shapes
    ├── repositories/        # DynamoDB accessors — table client + per-aggregate helpers
    └── services/            # Use-case-level orchestration (cross-item transactions, domain invariants)
```

The split into `api / models / repositories / services` is a stack-level
choice that follows from FastAPI + DynamoDB. The concrete modules inside each
folder will be filled in once the entity model and use case specs land —
naming them now would prejudge both.

## 5. Frontend structure (Angular)

- Standalone components, signal-based state where useful.
- HTTP client services generated from the FastAPI OpenAPI schema using
  `ng-openapi-gen` or `openapi-generator-cli` — keeps backend and frontend
  contracts in lockstep.
- Top-level feature areas align to the four actors from `vision.md`:
  `booking/` (Guest), `reception/` (Receptionist), `housekeeping/`
  (Housekeeping), `management/` (Manager). The exact screens within each
  area follow from the use case specifications.

## 6. Email (FR-003, FR-009)

Confirmation and reminder emails are out of scope for this initial cut.
When implemented:

- **Production:** Amazon SES with verified sender + DKIM.
- **Local dev:** stub to log/file, or run [LocalStack](https://localstack.cloud/)
  alongside DynamoDB Local for SES emulation.
- The reminder flow (FR-009) requires a scheduler (e.g. EventBridge → Lambda,
  or cron → backend); the trigger mechanism is decided alongside the use case
  spec.

## 7. Decisions deferred to later phases

- **Entity model** — entities, attributes, identifiers, and relationships.
  Drives the Pydantic model layer and the DynamoDB physical schema.
- **Use case specifications** — per-FR flows, preconditions, postconditions,
  and invariants. Drives router/service module names and the access-pattern
  catalog the DynamoDB key design must support.
- **DynamoDB physical design** — single-table vs. multi-table, partition/sort
  key strategy, GSIs. Cannot be settled until the access patterns are known
  from the use cases.
- **Identifier strategy** — natural keys vs. ULIDs vs. UUIDs. Decided with
  the entity model.
- **Authentication / authorization** (Cognito vs. self-hosted JWT) —
  explicitly deferred; out of scope until the use cases that need a
  logged-in actor are specified.
- **Scaffolding the Angular workspace and FastAPI skeleton** — the layouts
  in §2 and §4 are the target; generation is a separate task.
