"""
Data model for a Digital Identity record and supporting enums.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import date
from typing import List, Tuple, Optional


class IDStatus(Enum):
    """Possible lifecycle states for a Digital ID."""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


class OrganisationType(Enum):
    """Types of organisation that interact with the Digital ID platform."""
    CENTRAL_AUTHORITY = "CENTRAL_AUTHORITY"
    TAX_AUTHORITY = "TAX_AUTHORITY"
    DRIVING_LICENCE_AUTHORITY = "DRIVING_LICENCE_AUTHORITY"
    EMPLOYER = "EMPLOYER"
    BANK = "BANK"
    WELFARE_SERVICE = "WELFARE_SERVICE"
    LOCAL_AUTHORITY = "LOCAL_AUTHORITY"
    IMMIGRATION = "IMMIGRATION"


@dataclass
class DigitalID:
    """
    A single Digital Identity record.

    Immutable fields (set once at creation):
        id_number, full_name, date_of_birth, nationality

    Mutable fields (updated only via IdentityService):
        address, email, has_restriction, status, suspension_history
    """
    # -- immutable --
    id_number: str
    full_name: str
    date_of_birth: date
    nationality: str
    # -- mutable --
    address: str
    email: str
    status: IDStatus = IDStatus.PENDING
    has_restriction: bool = False
    created_date: date = field(default_factory=date.today)
    suspension_history: List[Tuple[date, Optional[date]]] = field(default_factory=list)

    def is_active(self) -> bool:
        """Check if this Digital ID is in ACTIVE status."""
        return self.status == IDStatus.ACTIVE

    def was_suspended_during(self, start_date: date, end_date: date) -> bool:
        """Return True if any suspension overlaps with [start_date, end_date]."""
        for (susp_start, susp_end) in self.suspension_history:
            overlap_start = max(susp_start, start_date)
            overlap_end = min(susp_end if susp_end else end_date, end_date)
            if overlap_start <= overlap_end:
                return True
        return False

    def __str__(self) -> str:
        return (
            f"DigitalID[{self.id_number}] {self.full_name} | "
            f"DOB: {self.date_of_birth} | Status: {self.status.value} | "
            f"Restriction: {self.has_restriction}"
        )
