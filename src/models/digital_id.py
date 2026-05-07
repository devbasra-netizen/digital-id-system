"""Digital ID record and the enums it depends on."""

from enum import Enum
from dataclasses import dataclass, field
from datetime import date
from typing import ClassVar, List, Optional, Set, Tuple


class IDStatus(Enum):
    """Lifecycle states a Digital ID can hold."""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


class OrganisationType(Enum):
    """Organisation roles recognised by the platform."""
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
    """A single Digital Identity record.

    Immutable after creation:
        id_number, full_name, date_of_birth, nationality, created_date

    Mutable through IdentityService only:
        address, email, status, has_restriction, suspension_history
    """
    id_number: str
    full_name: str
    date_of_birth: date
    nationality: str
    address: str
    email: str
    status: IDStatus = IDStatus.PENDING
    has_restriction: bool = False
    created_date: date = field(default_factory=date.today)
    suspension_history: List[Tuple[date, Optional[date]]] = field(default_factory=list)
    _is_initialized: bool = field(default=False, init=False, repr=False)

    _IMMUTABLE_FIELDS: ClassVar[Set[str]] = {
        "id_number",
        "full_name",
        "date_of_birth",
        "nationality",
        "created_date",
    }

    def __post_init__(self) -> None:
        # Flip the flag last so the immutability guard only activates once
        # construction has finished (otherwise the dataclass init would trip it).
        object.__setattr__(self, "_is_initialized", True)

    def __setattr__(self, name: str, value) -> None:
        if getattr(self, "_is_initialized", False) and name in self._IMMUTABLE_FIELDS:
            raise AttributeError(f"'{name}' is immutable and cannot be changed once set.")
        object.__setattr__(self, name, value)

    def is_active(self) -> bool:
        return self.status == IDStatus.ACTIVE

    def was_suspended_during(self, start_date: date, end_date: date) -> bool:
        """True if any suspension period overlaps [start_date, end_date].

        An open-ended suspension (end is None) is treated as still ongoing.
        """
        for (susp_start, susp_end) in self.suspension_history:
            suspension_end = susp_end if susp_end is not None else date.max
            if susp_start <= end_date and start_date <= suspension_end:
                return True
        return False

    def __str__(self) -> str:
        return (
            f"DigitalID[{self.id_number}] {self.full_name} | "
            f"DOB: {self.date_of_birth} | Status: {self.status.value} | "
            f"Restriction: {self.has_restriction}"
        )
