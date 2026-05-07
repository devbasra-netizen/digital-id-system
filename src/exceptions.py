"""Custom exception hierarchy for the Digital ID system.

Each project-specific exception also inherits from a related Python built-in,
so callers can either catch the specific class or the broad built-in type.
"""

import builtins


class DigitalIDError(Exception):
    """Base class for all errors raised by this system."""
    pass


class ValidationError(DigitalIDError, ValueError):
    """Raised when an input value fails a validation check."""
    pass


class InvalidOperationError(DigitalIDError, ValueError):
    """Raised when an operation is not valid for the current state."""
    pass


class PermissionError(DigitalIDError, builtins.PermissionError):
    """Raised when an organisation is not authorised for an operation."""
    pass


class IDNotFoundError(DigitalIDError, KeyError):
    """Raised when no Digital ID exists for the given id_number."""
    pass
