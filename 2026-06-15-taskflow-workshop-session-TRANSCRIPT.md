# Session Transcript — TaskFlow Workshop Session

> **Project:** TaskFlow API (Claude Code workshop)
> **Date:** 2026-06-15
> **Scope:** Project walkthrough, a new utility + tests, git/remote operations,
> an architecture explanation, error logging across write endpoints, and a new
> workshop exercise on persistence.

---

## Contents
1. What does this project do?
2. What does CLAUDE.md do for this project?
3. Add `format_task_id` utility
4. Add a unit test for it
5. Commit the two changes (feature branch + commit skill)
6. Write & commit a transcript of part 1
7. Inspect git remotes
8. Repoint `origin` to a new org repo, keep original as `upstream`
9. Merge `feat/format-task-id` into local `main`
10. Delete the merged branch
11. Change the `origin` remote URL (repo rename)
12. Explain the architecture
13. Add error logging to the task-creation endpoint
14. Wire up logging config + extend error logging to update/delete/assign
15. How to exercise the API without a GUI
16. Where the data is actually stored
17. Create exercise `03b-persistent-data-stores.md`

---

## 1. What does this project do?

Read `main.py`, `models.py`, `routers/tasks.py`, `database.py`.

**TaskFlow API** is a task-management REST API built with **FastAPI** (Python),
a teaching codebase for a Claude Code workshop. Two resources — **Tasks**
(title, description, priority, status, assignee, tags, timestamps) and **Users**
(username, display name, email) — modeled with Pydantic. Task endpoints under
`/api/v1/tasks` cover list (with filters + pagination), create (201), stats,
get (404 if missing), patch, delete (204), and assign. Storage is an in-memory
`dict`-based `TaskDatabase`, seeded with 3 users and 5 tasks on startup.

Key point: thin routers, business logic in the database layer; separate
Create/Update/Read Pydantic models prevent clients from setting server-owned
fields. Run with `uv run uvicorn taskflow.main:app --reload`, docs at `/docs`.

---

## 2. What does CLAUDE.md do for this project?

`CLAUDE.md` is auto-loaded into context at the start of every session and is
checked into git, so the whole team's Claude shares the same rules — a
project-specific system prompt / "house rules for the AI." It supplies: build &
run commands (the project uses `uv`), a file-by-file architecture map, and the
conventions to imitate (thin handlers, `str | None`, proper status codes).
There are two stacked files — this project one plus a user-level
`~/.claude/CLAUDE.md`; the more specific project file wins on overlap.

---

## 3. Add `format_task_id` utility

Read `utils.py` to match its style (concise functions, full type hints,
one-line docstrings). Added to `src/taskflow/utils.py`:

```python
def format_task_id(number: int) -> str:
    """Format an integer as a zero-padded task ID like 'TASK-001'."""
    return f"TASK-{number:03d}"
```

Verified: `1 → TASK-001`, `42 → TASK-042`, `1000 → TASK-1000` (the `03d` width
is a minimum, not a cap). Parameter named `number` to avoid shadowing the `id`
builtin. Noted nothing calls it yet (real IDs are UUIDs).

---

## 4. Add a unit test for it

A ruff `check --fix` hook stripped the import on the first pass (unused until
referenced), so the test function was added first, then the import. Added to
`tests/test_utils.py`:

```python
def test_format_task_id():
    assert format_task_id(1) == "TASK-001"
    assert format_task_id(42) == "TASK-042"
    assert format_task_id(999) == "TASK-999"
    assert format_task_id(1000) == "TASK-1000"
    assert format_task_id(0) == "TASK-000"
```

`uv run pytest tests/test_utils.py::test_format_task_id -v` → **1 passed**.
Lesson: a post-Edit ruff hook removes unused imports — land the usage before (or
with) the import.

---

## 5. Commit the two changes

Invoked the `commit` skill (Sentry conventions). We were on `main`, so per the
skill a feature branch was created first:

- `git checkout -b feat/format-task-id`
- Staged only the two files (left the untracked `.code-workspace` out)
- Commit `ffd277b`: `feat(utils): Add format_task_id helper`

---

## 6. Write & commit a transcript of part 1

Wrote `2026-06-11-format-task-id-TRANSCRIPT.md` (a faithful, condensed
reconstruction — full tool dumps summarized). Committed on the same branch as
`f400b19`: `docs: Add session transcript for format_task_id work`.

---

## 7. Inspect git remotes

`git remote -v` showed a single remote:
`origin → https://github.com/zachschillaci27/claude-code-workshop.git`
(an upstream workshop repo, likely not directly pushable).

---

## 8. Repoint `origin` to a new org repo, keep original as `upstream`

Provided the commands (and corrected the URL: the GitHub `/orgs/...` path is a
web-UI path, not a valid git remote URL):

```bash
git remote rename origin upstream
git remote add origin https://github.com/AI-Training-Projects/claude-code-workshop.git
git remote -v
```

Result: `origin` = new AI-Training-Projects repo (push here), `upstream` =
original (pull updates). Convention only; renaming preserves existing refs.

---

## 9. Merge `feat/format-task-id` into local `main`

`git checkout main` then `git merge feat/format-task-id` → **fast-forward**
(main had no divergent commits), moving `ffd277b` and `f400b19` onto `main`.
Main ended 2 commits ahead of `upstream/main` (local only, not pushed).

---

## 10. Delete the merged branch

`git branch -d feat/format-task-id` → deleted safely (the `-d` form refuses
unless fully merged; nothing lost). Left on `main` with no other local branches.

---

## 11. Change the `origin` remote URL (repo rename)

To repoint `origin` from `claude-code-workshop.git` to the renamed repo:

```bash
git remote set-url origin https://github.com/AI-Training-Projects/PydanticAI-FastAPI-Workshop.git
git remote -v
```

`set-url` changes WHERE a remote points (vs `rename` = label, `add` = new
remote). Local-only config edit; the target repo must exist before first push.

---

## 12. Explain the architecture

Read `routers/users.py` and listed all tracked source/test files.

Layered architecture with a strict one-directional dependency:
**Router (thin) → Data layer (TaskDatabase, all logic) → Models (Pydantic)**,
with `utils.py` as pure stateless helpers. Traced `POST /api/v1/tasks` through
the layers. Four key decisions: thin routers/fat data layer; three models per
resource (Create/Update/Read); the database as a swappable seam (single global
`db`, dict-backed, the one workshop-only shortcut); routers as composable
modules mounted under `/api/v1`. Tests mirror the layers (utils unit, models
validation, tasks end-to-end via the `client` fixture).

---

## 13. Add error logging to the task-creation endpoint

No existing logging in the codebase, so added the idiomatic
`logger = logging.getLogger(__name__)` to `routers/tasks.py` and wrapped
creation:

```python
@router.post("", response_model=Task, status_code=201)
def create_task(data: TaskCreate) -> Task:
    """Create a new task."""
    try:
        task = db.create_task(data)
    except Exception:
        logger.exception("Failed to create task with title %r", data.title)
        raise HTTPException(status_code=500, detail="Failed to create task")
    logger.info("Created task %s (%r)", task.id, task.title)
    return task
```

Used `logger.exception` (captures traceback) and lazy `%` formatting (logging
convention). Caveats surfaced: `db.create_task` can't realistically fail yet
(defensive); and nothing emits until logging is configured. All 9 task tests
passed.

---

## 14. Wire up logging config + extend error logging

**(1)** Added to `main.py`:

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
```

**(2)** Applied the same pattern to `update_task`, `delete_task`, and
`assign_task`. Critical design point: keep the **404 checks outside** the
`try`, because `HTTPException` subclasses `Exception` — wrapping the whole body
would relabel a legitimate 404 as a 500.

Verified: full suite **19 passed**, `ruff check src/` clean. Live smoke test
confirmed real output —
`INFO taskflow.routers.tasks - Created task dc865ee4… ('Logging smoke test')` —
and that a PATCH on a missing task correctly returned **404, not 500**.

---

## 15. How to exercise the API without a GUI

The API already has a GUI: FastAPI's auto-generated **Swagger UI at `/docs`**
("Try it out" sends real requests), plus `/redoc`. Other workouts: the pytest
suite (19 tests, end-to-end, no server needed), `curl`/httpie against a running
server, and a potential `scripts/smoke_test.py` that walks the full lifecycle
(create → list/filter → update → assign → stats → delete → verify 404s). With
the new logging, INFO lines stream as you hit endpoints. (Offered to build the
smoke-test script.)

---

## 16. Where the data is actually stored

**There is no file.** Data lives in RAM inside the running process — two Python
dicts (`_tasks`, `_users`) held by the global `db = TaskDatabase()` in
`database.py`. Lifetime = the process: restart (or any `--reload` save) resets
to seed data, and separate uvicorn workers each get their own dict. The file's
own docstring admits this is workshop-only. To persist, swap the in-memory
store for SQLite, a JSON file, or SQLAlchemy+Postgres — a localized change
thanks to the layering. (Offered to convert to SQLite.)

---

## 17. Create exercise `03b-persistent-data-stores.md`

Read `03-settings-and-permissions.md` to match the workshop format
(Goal → Concepts → numbered Tasks → Key Takeaways) and the folder convention
(no version header). Wrote `exercises/03b-persistent-data-stores.md` with six
progressive tasks: 3b.1 baseline (prove ephemerality) → 3b.2 JSON file →
3b.3 **SQLite** (core) → 3b.4 per-request store via `Depends` → 3b.5 seed &
migrations → 3b.6 docs + commit. Built around the architectural seam: every task
insists `TaskDatabase` method signatures stay identical so the existing 19 tests
act as the regression net. Includes a verification checklist.

---

## Artifacts & Git State at Session End

**Committed (on `main`, fast-forwarded, local only — not pushed):**
- `ffd277b` feat(utils): Add format_task_id helper
- `f400b19` docs: Add session transcript for format_task_id work

**Uncommitted working changes (from this session):**
- `src/taskflow/routers/tasks.py` — error logging on create/update/delete/assign
- `src/taskflow/main.py` — logging.basicConfig
- `exercises/03b-persistent-data-stores.md` — new exercise (untracked)
- `2026-06-15-taskflow-workshop-session-TRANSCRIPT.md` — this file (untracked)

**Remotes (as discussed; commands provided, run by user):**
- `origin` → AI-Training-Projects repo (final target: `PydanticAI-FastAPI-Workshop.git`)
- `upstream` → `zachschillaci27/claude-code-workshop.git`

**Suggested next steps:**
- Commit the logging changes on a feature branch (e.g. `feat/error-logging`)
- Optionally add tests asserting update/delete on a missing task return 404
- Build `scripts/smoke_test.py` for a repeatable full workout
- Tackle exercise 03b to add real persistence
