"""
Sets test environment variables BEFORE any app module is imported, since
app.core.config.Settings() reads os.environ once at import time (import
is cached — reloading it later to pick up new env vars is fragile and,
in a multi-module app, actually causes stale-reference bugs: other
modules that already did `from app.core.config import settings` keep
pointing at the pre-reload instance). Setting env vars here, before
collection imports anything, avoids that entirely.
"""

import os

os.environ.setdefault("USE_MOCK_IMD", "true")
os.environ.setdefault("ENABLE_SCHEDULER", "false")
os.environ.setdefault("ADMIN_API_KEY", "test-admin-key")
os.environ.setdefault("INGEST_TOKEN", "dev-ingest-token")
