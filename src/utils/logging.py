"""
Simple logging utilities for the application.

Provides consistent logging across all modules without external dependencies.
"""


def log_info(msg: str) -> None:
    """Log an informational message."""
    print(f"[INFO] {msg}")


def log_error(msg: str) -> None:
    """Log an error message."""
    print(f"[ERROR] {msg}")


def log_debug(msg: str) -> None:
    """Log a debug message."""
    print(f"[DEBUG] {msg}")


def log_warning(msg: str) -> None:
    """Log a warning message."""
    print(f"[WARNING] {msg}")
