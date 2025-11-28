"""
Background tasks package

Expose `start_background_tasks` and `stop_background_tasks` for application lifecycle.

Usage:
    from background_tasks import start_background_tasks, stop_background_tasks

This package contains the actual runner implementation in `runner.py`.
"""

from .runner import start_background_tasks, stop_background_tasks

__all__ = ["start_background_tasks", "stop_background_tasks"]
