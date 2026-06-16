"""Task management endpoints."""

import logging

from fastapi import APIRouter, HTTPException, Query

from taskflow.database import db
from taskflow.models import (
    Priority,
    Task,
    TaskCreate,
    TaskStatus,
    TaskUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[Task])
def list_tasks(
    status: TaskStatus | None = None,
    priority: Priority | None = None,
    assignee: str | None = None,
    tag: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Task]:
    """List tasks with optional filters."""
    tasks = db.list_tasks(status=status, priority=priority, assignee=assignee, tag=tag)
    return tasks[offset : offset + limit]


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


@router.get("/stats")
def get_task_stats() -> dict:
    """Get task statistics."""
    return db.get_task_stats()


@router.get("/{task_id}", response_model=Task)
def get_task(task_id: str) -> Task:
    """Get a single task by ID."""
    task = db.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.patch("/{task_id}", response_model=Task)
def update_task(task_id: str, data: TaskUpdate) -> Task:
    """Update a task."""
    try:
        task = db.update_task(task_id, data)
    except Exception:
        logger.exception("Failed to update task %s", task_id)
        raise HTTPException(status_code=500, detail="Failed to update task")
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    logger.info("Updated task %s", task_id)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: str) -> None:
    """Delete a task."""
    try:
        deleted = db.delete_task(task_id)
    except Exception:
        logger.exception("Failed to delete task %s", task_id)
        raise HTTPException(status_code=500, detail="Failed to delete task")
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    logger.info("Deleted task %s", task_id)


@router.post("/{task_id}/assign", response_model=Task)
def assign_task(task_id: str, assignee: str = Query(...)) -> Task:
    """Assign a task to a user."""
    user = db.get_user_by_username(assignee)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User '{assignee}' not found")

    try:
        task = db.update_task(task_id, TaskUpdate(assignee=assignee))
    except Exception:
        logger.exception("Failed to assign task %s to %r", task_id, assignee)
        raise HTTPException(status_code=500, detail="Failed to assign task")
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    logger.info("Assigned task %s to %r", task_id, assignee)
    return task
