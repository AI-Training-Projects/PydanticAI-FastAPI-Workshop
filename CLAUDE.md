# TaskFlow API

A Python FastAPI task management API used for the Claude Code workshop.

## Build & Run

- Install: `uv sync`
- Run server: `uv run uvicorn taskflow.main:app --reload`
- Run tests: `uv run pytest`
- Run single test: `uv run pytest tests/test_tasks.py::test_create_task -v`
- Lint: `uv run ruff check src/ tests/`
- Format: `uv run ruff format src/ tests/`

## Architecture

- `src/taskflow/main.py` - FastAPI app entry point
- `src/taskflow/models.py` - Pydantic request/response models
- `src/taskflow/database.py` - In-memory database with seed data
- `src/taskflow/routers/tasks.py` - Task CRUD endpoints
- `src/taskflow/routers/users.py` - User endpoints
- `src/taskflow/utils.py` - Helper functions
- `tests/` - Pytest test suite

## Code Conventions

- Use type hints on all function signatures
- Prefer `str | None` over `Optional[str]`
- Keep endpoint handlers thin - business logic goes in database layer
- Tests use the `client` fixture from `conftest.py`
- Sort imports with `ruff` (isort-compatible)

## API Design

- All endpoints are under `/api/v1/`
- Use proper HTTP status codes (201 for create, 204 for delete)
- Return 404 with detail message for missing resources
- Use query parameters for filtering, not request body


## Error Handling
- Always use `HTTPException` from FastAPI for error responses
- Include a `detail` field with a human-readable message
- Log errors with `import logging; logger = logging.getLogger(__name__)`
