"""
Compatibility shim for `services.background_tasks`.

Background tasks implementation was moved to the top-level
`backend/background_tasks` package to separate concerns. This module
remains as a thin shim so existing imports continue to work while
emitting a deprecation warning.
"""

from background_tasks import start_background_tasks, stop_background_tasks
from services.logger import AppLogger

logger = AppLogger.get_logger(__name__)

logger.info("Imported background tasks shim; implementation moved to 'background_tasks' package")

__all__ = ["start_background_tasks", "stop_background_tasks"]
