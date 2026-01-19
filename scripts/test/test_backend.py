#!/usr/bin/env python3
"""
Simple backend test script
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import uvicorn

if __name__ == "__main__":
    # Run with reload disabled for stability
    uvicorn.run(
        "src.app:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
        access_log=True
    )
