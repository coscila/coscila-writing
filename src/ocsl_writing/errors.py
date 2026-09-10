"""Actionable errors suitable for CLI and MCP clients."""


class WritingError(Exception):
    pass


class ValidationError(WritingError):
    pass


class TrustBoundaryError(WritingError):
    pass
