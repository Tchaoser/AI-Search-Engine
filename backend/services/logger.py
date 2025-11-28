"""
Centralized logging module for the AI-Search-Engine backend.

This module provides a standardized logging system with file and console handlers,
proper log formatting, and rotation. It is NOT visible to clients and should be used
for all backend diagnostic and operational logging.

USAGE:
------
Import the logger singleton in any module:

    from services.logger import logger

Then use standard Python logging methods:

    logger.info("User search initiated", extra={"user_id": user.id, "query": q})
    logger.warning("Cache miss for query", extra={"query": q})
    logger.error("API call failed", extra={"endpoint": url, "status": status}, exc_info=True)
    logger.debug("Profile rebuilt with 42 tokens", extra={"user_id": uid})

Log Levels:
-----------
- DEBUG: Detailed information for diagnosing problems (e.g., cache operations, token counts)
- INFO: General informational messages (e.g., search initiated, profile updated, auth success)
- WARNING: Warning messages for unexpected but recoverable situations (e.g., API timeouts, missing cache)
- ERROR: Error messages for serious problems that need attention (e.g., API failures, DB errors)
- CRITICAL: Critical errors that may cause system failure (e.g., DB connection loss, JWT signing failure)

Log Format:
-----------
File logs: %(asctime)s | %(levelname)-8s | %(name)s | %(message)s
Console logs: %(levelname)-8s | %(name)s | %(message)s

Structured Logging with 'extra':
--------------------------------
Pass a dict as the 'extra' parameter to include structured context in logs:

    logger.info("Search completed", extra={
        "user_id": user_id,
        "query": query,
        "result_count": len(results),
        "duration_ms": elapsed_time
    })

This produces: "INFO | api.search | Search completed (user_id=user123, query=python, result_count=10, duration_ms=245)"

File Output:
-----------
Logs are written to: backend/logs/app.log
Rotation occurs at 10 MB per file, with 5 backup files retained.
Log directory is created automatically if it doesn't exist.

Examples by Component:
----------------------

# Search API (api/search_routes.py)
logger.info("Search request", extra={
    "user_id": user_id,
    "query": q,
    "use_enhanced": use_enhanced
})
logger.debug("Search results ranked", extra={
    "user_id": user_id,
    "result_count": len(results),
    "top_result": results[0].get("title") if results else None
})

# Query Expansion (services/semantic_expansion.py)
logger.debug("Query expansion", extra={
    "original": seed,
    "expanded": expanded,
    "cache_hit": in_cache
})

# Authentication (services/auth_service.py)
logger.info("User login successful", extra={"username": username})
logger.warning("Login failed", extra={"username": username, "reason": "invalid_password"})
logger.error("Password hashing failed", extra={"username": username}, exc_info=True)

# Profile Operations (api/profile_routes.py)
logger.info("Explicit interest added", extra={
    "user_id": user_id,
    "keyword": keyword,
    "weight": weight
})
logger.debug("Profile built", extra={
    "user_id": user_id,
    "implicit_count": len(implicit),
    "explicit_count": len(explicit)
})

# Interactions (api/search_routes.py)
logger.info("Click logged", extra={
    "user_id": user_id,
    "query_id": query_id,
    "url": clicked_url,
    "rank": rank
})

# Database Operations (services/db.py)
logger.debug("Database connected", extra={"db_name": DB_NAME})
logger.error("Database query failed", extra={
    "collection": "queries",
    "operation": "insert"
}, exc_info=True)

# Background Tasks (services/background_tasks.py)
logger.info("Profile rebuild cycle", extra={
    "user_count": len(user_ids),
    "success_count": success,
    "failure_count": failure,
    "duration_s": elapsed
})
"""

import os
import logging
import logging.handlers
from pathlib import Path


def _get_logger(name: str) -> logging.Logger:
    """
    Create and configure a logger instance with file and console handlers.
    
    Args:
        name: Logger name (typically __name__ or module name)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure once (check if handlers already exist)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app.log"
    
    # Formatter
    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_formatter = logging.Formatter(
        fmt="%(levelname)-8s | %(name)s | %(message)s"
    )
    
    # File handler with rotation (10 MB per file, keep 5 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Only show INFO and above on console
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


class AppLogger:
    """
    Singleton logger factory for the application.
    
    Provides a consistent logger interface across all modules with
    automatic handling of 'extra' parameter formatting.
    """
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get or create a logger with the given name.
        
        Args:
            name: Logger name (typically module name)
            
        Returns:
            Configured logger instance
        """
        if name not in cls._loggers:
            cls._loggers[name] = _get_logger(name)
        return cls._loggers[name]


# Create default logger for services
logger = AppLogger.get_logger("app")


def format_extra(extra_dict: dict) -> str:
    """
    Format extra parameters for display in log messages.
    
    Args:
        extra_dict: Dictionary of key-value pairs to format
        
    Returns:
        Formatted string like "key1=value1, key2=value2"
    """
    if not extra_dict:
        return ""
    items = [f"{k}={v}" for k, v in extra_dict.items()]
    return " (" + ", ".join(items) + ")"


# Monkey-patch logger methods to support formatted extra parameters
_original_info = logger.info
_original_debug = logger.debug
_original_warning = logger.warning
_original_error = logger.error
_original_critical = logger.critical


def _log_with_extra(original_method, level_name):
    def wrapper(msg, *args, **kwargs):
        extra = kwargs.pop("extra", None)
        if extra and isinstance(extra, dict):
            msg = msg + format_extra(extra)
        original_method(msg, *args, **kwargs)
    return wrapper


logger.info = _log_with_extra(_original_info, "INFO")
logger.debug = _log_with_extra(_original_debug, "DEBUG")
logger.warning = _log_with_extra(_original_warning, "WARNING")
logger.error = _log_with_extra(_original_error, "ERROR")
logger.critical = _log_with_extra(_original_critical, "CRITICAL")
