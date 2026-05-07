"""Append-only audit log used by both services."""

from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass(frozen=True)
class AuditEntry:
    """A single audit record. Frozen so old entries cannot be edited."""
    timestamp: datetime
    organisation: str
    operation: str
    id_number: str
    details: str
    success: bool


class AuditLog:
    """Append-only log of system activity.

    Entries are never modified or deleted once recorded. The query
    helpers below are read-only views on the underlying list.
    """

    def __init__(self) -> None:
        self._entries: List[AuditEntry] = []

    def record(
        self,
        organisation: str,
        operation: str,
        id_number: str,
        details: str,
        success: bool,
    ) -> None:
        """Append a new entry stamped with the current time."""
        entry = AuditEntry(
            timestamp=datetime.now(),
            organisation=organisation,
            operation=operation,
            id_number=id_number,
            details=details,
            success=success,
        )
        self._entries.append(entry)

    # Query helpers

    def get_entries_for_id(self, id_number: str) -> List[AuditEntry]:
        return [e for e in self._entries if e.id_number == id_number]

    def get_entries_by_operation(self, operation: str) -> List[AuditEntry]:
        return [e for e in self._entries if e.operation == operation]

    def get_entries_by_organisation(self, organisation: str) -> List[AuditEntry]:
        return [e for e in self._entries if e.organisation == organisation]

    def get_failed_entries(self) -> List[AuditEntry]:
        return [e for e in self._entries if not e.success]

    def get_successful_entries(self) -> List[AuditEntry]:
        return [e for e in self._entries if e.success]

    def get_all_entries(self) -> List[AuditEntry]:
        return list(self._entries)

    def get_entries_count(self) -> int:
        return len(self._entries)

    def display(self) -> None:
        """Print the full log to the console (used by the demo script)."""
        if not self._entries:
            print("No audit entries recorded.")
            return
        print("\n" + "=" * 70)
        print("AUDIT LOG")
        print("=" * 70)
        for entry in self._entries:
            status_marker = "OK" if entry.success else "FAIL"
            print(
                f"[{entry.timestamp.strftime('%H:%M:%S')}] [{status_marker:4}] "
                f"{entry.organisation:25} | {entry.operation:25} | "
                f"ID: {entry.id_number:10} | {entry.details}"
            )
