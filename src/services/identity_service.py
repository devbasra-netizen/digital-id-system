"""
Identity Service — manages Digital ID lifecycle operations.

Only the central authority may create, update, or change the status of
Digital IDs.  All operations are validated, permission-checked, and
recorded in the audit log.
"""

from datetime import date
from typing import Dict, List
from src.models.digital_id import DigitalID, IDStatus
from src.auth.organisation_auth import OrganisationAuth
from src.audit.audit_log import AuditLog
from src.exceptions import InvalidOperationError, IDNotFoundError, PermissionError
from src.validators import (
    validate_id_number, validate_name, validate_email,
    validate_address, validate_date_of_birth, validate_nationality
)


class IdentityService:
    """
    Handles Digital ID lifecycle: create, activate, suspend, reinstate,
    revoke, and attribute updates.

    Status transitions:
        PENDING -> ACTIVE -> SUSPENDED -> ACTIVE (reinstate)
        Any non-revoked state -> REVOKED (terminal)
    """

    def __init__(self, audit_log: AuditLog) -> None:
        self._identities: Dict[str, DigitalID] = {}
        self._audit: AuditLog = audit_log

    @property
    def identities(self) -> Dict[str, DigitalID]:
        """Expose the identity store so VerificationService can read it."""
        return self._identities

    def _get_id_or_raise(self, id_number: str) -> DigitalID:
        """Look up an ID or raise IDNotFoundError."""
        if id_number not in self._identities:
            raise IDNotFoundError(f"Digital ID '{id_number}' does not exist.")
        return self._identities[id_number]

    def create_digital_id(
        self,
        auth: OrganisationAuth,
        id_number: str,
        full_name: str,
        date_of_birth: date,
        nationality: str,
        address: str,
        email: str,
    ) -> DigitalID:
        """
        Create a new Digital ID in PENDING status.

        Validates all inputs, checks for duplicate ID numbers, and records the
        operation in the audit log.  Only the Central Authority may call this.
        """
        try:
            auth.require_permission("create_id")
        except PermissionError as e:
            self._audit.record(auth.org_name, "CREATE_ID", id_number,
                               f"Failed: {str(e)}", False)
            raise

        # Validate all inputs
        validate_id_number(id_number)
        validate_name(full_name, "Full name")
        validate_date_of_birth(date_of_birth)
        validate_nationality(nationality)
        validate_address(address)
        validate_email(email)

        if id_number in self._identities:
            self._audit.record(auth.org_name, "CREATE_ID", id_number,
                               "Failed: ID already exists.", False)
            raise InvalidOperationError(f"Digital ID '{id_number}' already exists.")

        digital_id = DigitalID(
            id_number=id_number,
            full_name=full_name,
            date_of_birth=date_of_birth,
            nationality=nationality,
            address=address,
            email=email,
        )
        self._identities[id_number] = digital_id
        self._audit.record(auth.org_name, "CREATE_ID", id_number,
                           f"Created for {full_name}.", True)
        return digital_id

    def activate_id(self, auth: OrganisationAuth, id_number: str) -> DigitalID:
        """Set a PENDING or SUSPENDED ID to ACTIVE.  Idempotent if already ACTIVE."""
        try:
            auth.require_permission("change_status")
        except PermissionError as e:
            self._audit.record(auth.org_name, "ACTIVATE_ID", id_number,
                               f"Failed: {str(e)}", False)
            raise

        digital_id = self._get_id_or_raise(id_number)

        if digital_id.status == IDStatus.REVOKED:
            self._audit.record(auth.org_name, "ACTIVATE_ID", id_number,
                               "Failed: Cannot activate a revoked ID.", False)
            raise InvalidOperationError(f"Cannot activate a revoked Digital ID '{id_number}'.")

        if digital_id.status == IDStatus.ACTIVE:
            self._audit.record(auth.org_name, "ACTIVATE_ID", id_number,
                               "No change: already ACTIVE.", True)
            return digital_id

        digital_id.status = IDStatus.ACTIVE
        self._audit.record(auth.org_name, "ACTIVATE_ID", id_number,
                           "Status set to ACTIVE.", True)
        return digital_id

    def suspend_id(self, auth: OrganisationAuth, id_number: str) -> DigitalID:
        """Suspend an ACTIVE ID and open a new suspension-history record."""
        try:
            auth.require_permission("change_status")
        except PermissionError as e:
            self._audit.record(auth.org_name, "SUSPEND_ID", id_number,
                               f"Failed: {str(e)}", False)
            raise

        digital_id = self._get_id_or_raise(id_number)

        if digital_id.status == IDStatus.REVOKED:
            self._audit.record(auth.org_name, "SUSPEND_ID", id_number,
                               "Failed: Cannot suspend a revoked ID.", False)
            raise InvalidOperationError(f"Cannot suspend a revoked Digital ID '{id_number}'.")

        if digital_id.status == IDStatus.SUSPENDED:
            self._audit.record(auth.org_name, "SUSPEND_ID", id_number,
                               "No change: already SUSPENDED.", True)
            return digital_id

        if digital_id.status != IDStatus.ACTIVE:
            self._audit.record(
                auth.org_name, "SUSPEND_ID", id_number,
                f"Failed: ID must be ACTIVE to suspend. "
                f"Current: {digital_id.status.value}.", False)
            raise InvalidOperationError("Can only suspend an ACTIVE Digital ID.")

        digital_id.status = IDStatus.SUSPENDED
        digital_id.suspension_history.append((date.today(), None))
        self._audit.record(auth.org_name, "SUSPEND_ID", id_number,
                           "Status set to SUSPENDED.", True)
        return digital_id

    def reinstate_id(self, auth: OrganisationAuth, id_number: str) -> DigitalID:
        """Re-activate a SUSPENDED ID and close the open suspension record."""
        try:
            auth.require_permission("change_status")
        except PermissionError as e:
            self._audit.record(auth.org_name, "REINSTATE_ID", id_number,
                               f"Failed: {str(e)}", False)
            raise

        digital_id = self._get_id_or_raise(id_number)

        if digital_id.status != IDStatus.SUSPENDED:
            self._audit.record(
                auth.org_name, "REINSTATE_ID", id_number,
                f"Failed: ID must be SUSPENDED. "
                f"Current: {digital_id.status.value}.", False)
            raise InvalidOperationError("Can only reinstate a SUSPENDED Digital ID.")

        # Close the open suspension record
        if digital_id.suspension_history and digital_id.suspension_history[-1][1] is None:
            start = digital_id.suspension_history[-1][0]
            digital_id.suspension_history[-1] = (start, date.today())

        digital_id.status = IDStatus.ACTIVE
        self._audit.record(auth.org_name, "REINSTATE_ID", id_number,
                           "Status set to ACTIVE (reinstated).", True)
        return digital_id

    def revoke_id(self, auth: OrganisationAuth, id_number: str) -> DigitalID:
        """Permanently revoke a Digital ID — this is a terminal state."""
        try:
            auth.require_permission("change_status")
        except PermissionError as e:
            self._audit.record(auth.org_name, "REVOKE_ID", id_number,
                               f"Failed: {str(e)}", False)
            raise

        digital_id = self._get_id_or_raise(id_number)

        if digital_id.status == IDStatus.REVOKED:
            self._audit.record(auth.org_name, "REVOKE_ID", id_number,
                               "No change: already REVOKED.", True)
            return digital_id

        # Close any open suspension before revoking
        if digital_id.suspension_history and digital_id.suspension_history[-1][1] is None:
            start = digital_id.suspension_history[-1][0]
            digital_id.suspension_history[-1] = (start, date.today())

        digital_id.status = IDStatus.REVOKED
        self._audit.record(auth.org_name, "REVOKE_ID", id_number,
                           "Status set to REVOKED (terminal).", True)
        return digital_id

    def update_address(self, auth: OrganisationAuth, id_number: str, new_address: str) -> DigitalID:
        """Update the mutable address attribute."""
        try:
            auth.require_permission("update_id")
        except PermissionError as e:
            self._audit.record(auth.org_name, "UPDATE_ADDRESS", id_number,
                               f"Failed: {str(e)}", False)
            raise

        validate_address(new_address)
        digital_id = self._get_id_or_raise(id_number)

        if digital_id.status == IDStatus.REVOKED:
            self._audit.record(auth.org_name, "UPDATE_ADDRESS", id_number,
                               "Failed: Cannot update a revoked ID.", False)
            raise InvalidOperationError("Cannot update a revoked Digital ID.")

        digital_id.address = new_address
        self._audit.record(auth.org_name, "UPDATE_ADDRESS", id_number,
                           "Address updated.", True)
        return digital_id

    def update_email(self, auth: OrganisationAuth, id_number: str, new_email: str) -> DigitalID:
        """Update the mutable email attribute."""
        try:
            auth.require_permission("update_id")
        except PermissionError as e:
            self._audit.record(auth.org_name, "UPDATE_EMAIL", id_number,
                               f"Failed: {str(e)}", False)
            raise

        validate_email(new_email)
        digital_id = self._get_id_or_raise(id_number)

        if digital_id.status == IDStatus.REVOKED:
            self._audit.record(auth.org_name, "UPDATE_EMAIL", id_number,
                               "Failed: Cannot update a revoked ID.", False)
            raise InvalidOperationError("Cannot update a revoked Digital ID.")

        digital_id.email = new_email
        self._audit.record(auth.org_name, "UPDATE_EMAIL", id_number,
                           "Email updated.", True)
        return digital_id

    def set_restriction(self, auth: OrganisationAuth, id_number: str,
                        has_restriction: bool) -> DigitalID:
        """Set or clear a restriction flag on a Digital ID."""
        try:
            auth.require_permission("update_id")
        except PermissionError as e:
            self._audit.record(auth.org_name, "SET_RESTRICTION", id_number,
                               f"Failed: {str(e)}", False)
            raise

        digital_id = self._get_id_or_raise(id_number)

        if digital_id.status == IDStatus.REVOKED:
            self._audit.record(auth.org_name, "SET_RESTRICTION", id_number,
                               "Failed: Cannot update a revoked ID.", False)
            raise InvalidOperationError("Cannot update a revoked Digital ID.")

        digital_id.has_restriction = has_restriction
        self._audit.record(auth.org_name, "SET_RESTRICTION", id_number,
                           f"Restriction set to {has_restriction}.", True)
        return digital_id

    # -- Search / query methods --

    def find_ids_by_name(self, name_pattern: str) -> List[DigitalID]:
        """Find all Digital IDs matching a name pattern (case-insensitive substring match)."""
        pattern_lower = name_pattern.lower()
        return [d for d in self._identities.values()
                if pattern_lower in d.full_name.lower()]

    def find_ids_by_status(self, status: IDStatus) -> List[DigitalID]:
        """Find all Digital IDs with a specific status."""
        return [d for d in self._identities.values() if d.status == status]

    def find_ids_by_nationality(self, nationality: str) -> List[DigitalID]:
        """Find all Digital IDs with a specific nationality."""
        return [d for d in self._identities.values()
                if d.nationality == nationality]

    def get_all_ids(self) -> List[DigitalID]:
        """Get all Digital IDs in the system."""
        return list(self._identities.values())

    def count_ids(self) -> int:
        """Get the total count of Digital IDs in the system."""
        return len(self._identities)
