"""Logging configuration"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
    """
    Setup logger with console and file handlers

    Args:
        name: Logger name (usually __name__)
        log_file: Optional path to log file. If None, creates timestamped file in logs/

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Create formatters
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '[%(levelname)s] %(message)s'
    )

    # Console handler (INFO level)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (DEBUG level)
    if log_file is None:
        # Create timestamped log file
        logs_dir = Path(__file__).parent.parent / 'logs'
        logs_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = logs_dir / f'pipeline_{timestamp}.log'

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)

    return logger


def log_step_start(logger: logging.Logger, step_name: str):
    """Log start of pipeline step with clear separation"""
    separator = "=" * 60
    logger.info(f"\n{separator}")
    logger.info(f"  {step_name}")
    logger.info(separator)


def log_step_complete(logger: logging.Logger, step_name: str, duration: float):
    """Log completion of pipeline step with timing"""
    logger.info(f"✓ {step_name} complete ({duration:.2f}s)")
