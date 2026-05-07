"""Organisation-level permission checks.

Each service method calls require_permission() before doing any work,
so the same check is applied regardless of which portal is calling.
"""

from src.models.digital_id import OrganisationType
from src.config import get_permissions
from src.exceptions import PermissionError


class OrganisationAuth:
    """Wraps an organisation's type and name and exposes permission checks."""

    def __init__(self, org_type: OrganisationType, org_name: str) -> None:
        self.org_type: OrganisationType = org_type
        self.org_name: str = org_name

    def can_perform(self, operation: str) -> bool:
        """True if this organisation type may run the given operation."""
        return operation in get_permissions(self.org_type)

    def require_permission(self, operation: str) -> None:
        """Raise PermissionError if the caller is not authorised."""
        if not self.can_perform(operation):
            raise PermissionError(
                f"Organisation '{self.org_name}' ({self.org_type.value}) "
                f"is not authorised to perform '{operation}'."
            )
