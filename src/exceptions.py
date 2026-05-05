"""Project-specific exceptions for the Digital ID system."""

import builtins


class DigitalIDError(Exception):
    """Base class for system-specific errors."""
    pass


class ValidationError(DigitalIDError, ValueError):
    """Raised when input values do not pass checks."""
    pass


class InvalidOperationError(DigitalIDError, ValueError):
    """Raised when the requested action is not valid for current state."""
    pass


class PermissionError(DigitalIDError, builtins.PermissionError):
    """Raised when an organisation is not allowed to do an operation."""
    pass


class IDNotFoundError(DigitalIDError, KeyError):
    """Raised when an ID number does not exist in the store."""
    pass
