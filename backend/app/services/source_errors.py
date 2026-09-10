"""Errors raised when an environmental provider cannot supply a real reading."""


class DataSourceUnavailable(RuntimeError):
    """A required real-world data source is unavailable or misconfigured."""
