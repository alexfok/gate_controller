"""Logging utility for gate controller."""

import logging
import logging.handlers
import os
import threading
from typing import Optional

_pkg_file_lock = threading.Lock()


def _ensure_package_file_handler(log_file: str, level_num: int) -> None:
    """Attach one RotatingFileHandler to the ``gate_controller`` package logger.

    Child loggers propagate here so all modules share rotation instead of opening
    the same path multiple times.
    """
    pkg = logging.getLogger("gate_controller")
    with _pkg_file_lock:
        for h in pkg.handlers:
            if isinstance(h, logging.handlers.RotatingFileHandler):
                return
        try:
            os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
            # If config asks for DEBUG, keep file at INFO to avoid huge payloads (e.g. BCG04).
            file_level = logging.INFO if level_num == logging.DEBUG else level_num
            rot = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            rot.setLevel(file_level)
            rot.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
            pkg.addHandler(rot)
            pkg.setLevel(logging.DEBUG)
        except Exception as e:
            print(f"Warning: failed to create rotating log file {log_file}: {e}")


def get_logger(name: str, level: Optional[str] = None, log_file: Optional[str] = None) -> logging.Logger:
    """Get or create a logger instance.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path (rotating); shared across the package

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    level_str = level or os.getenv("LOG_LEVEL", "INFO")
    level_num = getattr(logging, level_str.upper(), logging.INFO)
    logger.setLevel(level_num)

    if log_file:
        _ensure_package_file_handler(log_file, level_num)

    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level_num)
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(console_handler)

    logger.propagate = True
    return logger
