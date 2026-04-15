"""
Organisation-level authorisation — checks whether an organisation is
allowed to perform a given operation.
"""

from src.models.digital_id import OrganisationType
from src.config import get_permissions
from src.exceptions import PermissionError


class OrganisationAuth:
    """
    Wraps an organisation's type and name and exposes permission checks.
    Every service method calls require_permission() before doing any work.
    """

    def __init__(self, org_type: OrganisationType, org_name: str) -> None:
        self.org_type: OrganisationType = org_type
        self.org_name: str = org_name

    def can_perform(self, operation: str) -> bool:
        """Return True if this organisation is allowed the given operation."""
        allowed: set[str] = get_permissions(self.org_type)
        return operation in allowed

    def require_permission(self, operation: str) -> None:
        """Raise PermissionError if the organisation is not authorised."""
        if not self.can_perform(operation):
            raise PermissionError(
                f"Organisation '{self.org_name}' ({self.org_type.value}) "
                f"is not authorised to perform '{operation}'."
            )
