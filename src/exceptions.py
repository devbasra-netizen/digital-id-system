"""
Custom exceptions for the Digital ID system.

Each exception inherits from both a base DigitalIDError and the closest
built-in type so that callers can catch either.
"""

import builtins


class DigitalIDError(Exception):
    """Base exception for all Digital ID system errors."""
    pass


class ValidationError(DigitalIDError, ValueError):
    """Raised when input data fails validation."""
    pass


class InvalidOperationError(DigitalIDError, ValueError):
    """Raised when an operation conflicts with the current ID state."""
    pass


class PermissionError(DigitalIDError, builtins.PermissionError):
    """Raised when an organisation is not authorised for an operation."""
    pass


class IDNotFoundError(DigitalIDError, KeyError):
    """Raised when a Digital ID cannot be found."""
    pass
