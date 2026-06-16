# Exercise 3b: Persistent Data Stores

## Goal
Replace TaskFlow's in-memory dictionary store with real, on-disk persistence so
data survives a server restart. Practice driving a contained, layered refactor
with Claude Code — and see why the "thin router / fat data layer" design makes
this a localized change.

## Background

Right now there is **no data file**. The entire database is two Python dicts
held in RAM by a single global object in
[`src/taskflow/database.py`](../src/taskflow/database.py):

```python
self._tasks: dict[str, Task] = {}
self._users: dict[str, User] = {}
...
db = TaskDatabase()   # one global instance, lives only while the process runs
```

Stop the server and everything resets to the seed data. Because every endpoint
goes through `db.*` methods (the routers never touch the dicts directly), the
storage backend can be swapped **without changing a single router**. That is the
property these tasks exploit.

## Concepts

| Option | Persists to | Server needed | Effort | When to use |
|--------|-------------|---------------|--------|-------------|
| In-memory dict (current) | Nothing (RAM) | No | — | Demos, tests |
| JSON file | `data/taskflow.json` | No | Low | Tiny apps, prototypes |
| SQLite | `taskflow.db` (one file) | No | Medium | Single-node real apps |
| SQLAlchemy + Postgres | Database server | Yes | High | Production, multi-worker |

**Key principle:** keep the public `TaskDatabase` method signatures identical
(`create_task`, `get_task`, `list_tasks`, `update_task`, `delete_task`, and the
user equivalents). If the interface stays stable, the routers and tests keep
working. Run `uv run pytest` after every task — the existing 19 tests are your
regression net.

## Tasks

### 3b.1 - Establish the Baseline
Confirm the current behavior before changing anything:
1. Start the server: `uv run uvicorn taskflow.main:app --reload`
2. `POST` a new task via `/docs` or curl.
3. Restart the server. Confirm your task is **gone** (back to 5 seed tasks).
4. Run `uv run pytest` and note all tests pass.

Ask Claude: "Explain exactly where the task data lives and why it disappears on
restart." Verify the answer against `database.py`.

### 3b.2 - JSON File Persistence (warm-up)
The simplest possible durability. Ask Claude to:
1. Add `_load()` / `_save()` helpers to `TaskDatabase` that serialize `_tasks`
   and `_users` to `data/taskflow.json` (use Pydantic's `model_dump` /
   `model_validate`; handle `datetime` and enum serialization).
2. Call `_save()` after every mutating method; call `_load()` in `__init__`
   (only seed if the file does not exist).
3. Add `data/` to `.gitignore`.

Verify: create a task, restart, confirm it **survives**. Run `uv run pytest`.

Discuss: what breaks if two requests write at once? (Hint: no locking.)

### 3b.3 - SQLite Persistence (the real exercise)
Swap the JSON store for SQLite — a single-file SQL database, no server.
Ask Claude to:
1. Add a dependency (`uv add sqlalchemy`), or use the stdlib `sqlite3` module
   if you want zero new deps.
2. Create the schema (a `tasks` table and a `users` table) and an engine
   pointing at `taskflow.db`.
3. Rewrite the `TaskDatabase` methods to run SQL queries instead of dict
   operations — **keeping the method signatures and return types identical**.
4. Translate filtering (`status`, `priority`, `assignee`, `tag`) into `WHERE`
   clauses, and `get_task_stats()` into `GROUP BY` aggregates.

Verify: all 19 tests still pass without modification. Inspect the data file:
```bash
sqlite3 taskflow.db ".tables"
sqlite3 taskflow.db "SELECT id, title, status FROM tasks;"
```

### 3b.4 - Decouple Storage Per Request (architecture)
The single global `db` is process-local and not concurrency-safe. Ask Claude to:
1. Introduce a FastAPI dependency (`Depends`) that yields a database/session
   per request instead of importing the global `db`.
2. Update the routers to receive the store via `Depends` rather than the module
   import.

Discuss: why does this matter the moment you run uvicorn with `--workers 2`?
(Tie back to "each process had its own dict" from the architecture walkthrough.)

### 3b.5 - Migrations & Seed Data
1. Decide how seed data should behave now that the DB persists — seed only on
   an empty database, never overwrite existing rows.
2. Sketch (or have Claude scaffold) a minimal migration path for when the
   schema changes (e.g. adding a column). Note where Alembic would fit if you
   went the SQLAlchemy route.

### 3b.6 - Document the Change
Update [`CLAUDE.md`](../CLAUDE.md) and [`README.md`](../README.md):
- Change the architecture note: `database.py` is now persistent, not in-memory.
- Document the data file location and how to reset it (delete the file).
- Add any new commands (e.g. inspecting the DB) to the Build & Run section.

Then write a session transcript and commit on a feature branch
(`feat/persistent-store`), per the project's git conventions.

## Verification Checklist
- [ ] A task created before a restart still exists after it
- [ ] `uv run pytest` — all tests pass, **unchanged**
- [ ] `uv run ruff check src/ tests/` — clean
- [ ] The data file is gitignored (no DB committed)
- [ ] `TaskDatabase` public method signatures are unchanged
- [ ] CLAUDE.md / README reflect the new persistence model

## Key Takeaways
- Clean layering pays off: a storage swap touches `database.py`, not the routers
- A stable interface + a regression test suite makes a risky refactor safe
- "Where is the data?" has three honest answers — RAM, a file, or a DB server —
  and the right one depends on durability and concurrency needs, not effort
- In-memory is perfect for a workshop; it is exactly wrong for production
- Let the existing tests drive the change: if they still pass, the swap is correct
