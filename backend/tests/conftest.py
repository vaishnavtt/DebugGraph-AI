"""
Pytest configuration and test fixtures for DebugGraph AI.
Ensures backend application modules are discoverable during test execution.
"""
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Ensure database tables exist for all test runs
from app.database.session import init_db
init_db()

