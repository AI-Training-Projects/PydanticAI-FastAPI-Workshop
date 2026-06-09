"""Tests for utility functions."""

from datetime import datetime, timedelta, timezone

from taskflow.utils import format_task_id, slugify, time_ago, truncate, validate_email


def test_slugify():
    assert slugify("Hello World") == "hello-world"
    assert slugify("  Spaces  Everywhere  ") == "spaces-everywhere"
    assert slugify("Special! @Characters#") == "special-characters"
    assert slugify("already-a-slug") == "already-a-slug"


def test_time_ago():
    now = datetime.now(timezone.utc)
    assert time_ago(now - timedelta(seconds=30)) == "just now"
    assert time_ago(now - timedelta(minutes=5)) == "5 minutes ago"
    assert time_ago(now - timedelta(minutes=1)) == "1 minute ago"
    assert time_ago(now - timedelta(hours=3)) == "3 hours ago"
    assert time_ago(now - timedelta(hours=1)) == "1 hour ago"
    assert time_ago(now - timedelta(days=2)) == "2 days ago"


def test_validate_email():
    assert validate_email("user@example.com") is True
    assert validate_email("first.last@domain.org") is True
    assert validate_email("not-an-email") is False
    assert validate_email("@missing.com") is False
    assert validate_email("missing@.com") is False


def test_truncate():
    assert truncate("short", 100) == "short"
    assert truncate("hello world", 8) == "hello..."
    assert len(truncate("x" * 200, 100)) == 100


def test_format_task_id():
    assert format_task_id(1) == "TASK-001"
    assert format_task_id(42) == "TASK-042"
    assert format_task_id(999) == "TASK-999"
    assert format_task_id(1000) == "TASK-1000"
    assert format_task_id(0) == "TASK-000"
