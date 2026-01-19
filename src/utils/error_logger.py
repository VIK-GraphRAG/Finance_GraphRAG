"""
Drone error logger utility
Writes errors to drone_error.log in the project root
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional
import traceback


def droneLogError(message: str, error: Optional[Exception] = None) -> None:
    """
    Append error details to drone_error.log

    Args:
        message: Human-readable error message
        error: Optional exception instance
    """
    try:
        droneLogPath = Path(__file__).resolve().parents[2] / "drone_error.log"
        timestamp = datetime.utcnow().isoformat()
        errorType = type(error).__name__ if error else "None"
        errorMessage = str(error) if error else ""
        errorTrace = traceback.format_exc() if error else ""

        with droneLogPath.open("a", encoding="utf-8") as logFile:
            logFile.write(f"{timestamp} | {message} | {errorType} | {errorMessage}\n")
            if errorTrace:
                logFile.write(errorTrace + "\n")
    except Exception:
        # Logging must never break the main flow
        pass
