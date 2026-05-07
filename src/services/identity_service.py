"""Identity Service: Digital ID lifecycle operations.

Only the central authority can create, update, or change the status of a
Digital ID. Every operation is permission-checked, validated, and logged
to the audit trail (including failures).
"""

from datetime import date
from typing import Dict, List
from src.models.digital_id import DigitalID, IDStatus
from src.auth.organisation_auth import OrganisationAuth
from src.audit.audit_log import AuditLog
from src.exceptions import (
    InvalidOperationError,
    IDNotFoundError,
    PermissionError,
    ValidationError,
)
from src.validators import (
    validate_id_number, validate_name, validate_email,
    validate_address, validate_date_of_birth, validate_nationality
)


class IdentityService:
    """Lifecycle operations for Digital IDs.

    Status flow:
        PENDING -> ACTIVE <-> SUSPENDED
        any non-revoked state -> REVOKED  (terminal)

    A few rules worth calling out:
        - suspend_id only accepts ACTIVE IDs
        - activate_id is idempotent for ACTIVE IDs
        - revoke_id is idempotent for REVOKED IDs
        - revoked IDs cannot be updated or transitioned again
    """

    def __init__(self, audit_log: AuditLog) -> None:
        self._identities: Dict[str, DigitalID] = {}
        self._audit: AuditLog = audit_log

    @property
    def identities(self) -> Dict[str, DigitalID]:
        """Read-only handle to the identity store, used by VerificationService."""
        return self._identities

    def _get_id_or_raise(self, id_number: str) -> DigitalID:
        if id_number not in self._identities:
            raise IDNotFoundError(f"Digital ID '{id_number}' does not exist.")
        return self._identities[id_number]

    def _lookup_for_operation(
        self, auth: OrganisationAuth, operation: str, id_number: str
    ) -> DigitalID:
        """Look up an ID and audit the failure path if it does not exist."""
        try:
            return self._get_id_or_raise(id_number)
        except IDNotFoundError as e:
            self._audit.record(auth.org_name, operation, id_number, f"Failed: {str(e)}", False)
            raise

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
        """Create a new Digital ID in PENDING status.

        Validates every input before mutating state, rejects duplicates, and
        logs the outcome. Only the Central Authority is authorised.
        """
        try:
            auth.require_permission("create_id")
        except PermissionError as e:
            self._audit.record(auth.org_name, "CREATE_ID", id_number,
                               f"Failed: {str(e)}", False)
            raise

        try:
            validate_id_number(id_number)
            validate_name(full_name, "Full name")
            validate_date_of_birth(date_of_birth)
            validate_nationality(nationality)
            validate_address(address)
            validate_email(email)
        except ValidationError as e:
            self._audit.record(auth.org_name, "CREATE_ID", id_number, f"Failed: {str(e)}", False)
            raise

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
        """Move a PENDING or SUSPENDED ID to ACTIVE. Idempotent if already ACTIVE."""
        try:
            auth.require_permission("change_status")
        except PermissionError as e:
            self._audit.record(auth.org_name, "ACTIVATE_ID", id_number,
                               f"Failed: {str(e)}", False)
            raise

        digital_id = self._lookup_for_operation(auth, "ACTIVATE_ID", id_number)

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
        """Suspend an ACTIVE ID and open a new entry in suspension_history."""
        try:
            auth.require_permission("change_status")
        except PermissionError as e:
            self._audit.record(auth.org_name, "SUSPEND_ID", id_number,
                               f"Failed: {str(e)}", False)
            raise

        digital_id = self._lookup_for_operation(auth, "SUSPEND_ID", id_number)

        if digital_id.status == IDStatus.REVOKED:
            self._audit.record(auth.org_name, "SUSPEND_ID", id_number,
                               "Failed: Cannot suspend a revoked ID.", False)
            raise InvalidOperationError(f"Cannot suspend a revoked Digital ID '{id_number}'.")

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

        digital_id = self._lookup_for_operation(auth, "REINSTATE_ID", id_number)

        if digital_id.status != IDStatus.SUSPENDED:
            self._audit.record(
                auth.org_name, "REINSTATE_ID", id_number,
                f"Failed: ID must be SUSPENDED. "
                f"Current: {digital_id.status.value}.", False)
            raise InvalidOperationError("Can only reinstate a SUSPENDED Digital ID.")

        # Close the still-open suspension record before flipping back to ACTIVE.
        if digital_id.suspension_history and digital_id.suspension_history[-1][1] is None:
            start = digital_id.suspension_history[-1][0]
            digital_id.suspension_history[-1] = (start, date.today())

        digital_id.status = IDStatus.ACTIVE
        self._audit.record(auth.org_name, "REINSTATE_ID", id_number,
                           "Status set to ACTIVE (reinstated).", True)
        return digital_id

    def revoke_id(self, auth: OrganisationAuth, id_number: str) -> DigitalID:
        """Permanently revoke a Digital ID. Terminal state."""
        try:
            auth.require_permission("change_status")
        except PermissionError as e:
            self._audit.record(auth.org_name, "REVOKE_ID", id_number,
                               f"Failed: {str(e)}", False)
            raise

        digital_id = self._lookup_for_operation(auth, "REVOKE_ID", id_number)

        if digital_id.status == IDStatus.REVOKED:
            self._audit.record(auth.org_name, "REVOKE_ID", id_number,
                               "No change: already REVOKED.", True)
            return digital_id

        # If currently suspended, close the open suspension period before revoking.
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

        try:
            validate_address(new_address)
        except ValidationError as e:
            self._audit.record(
                auth.org_name, "UPDATE_ADDRESS", id_number, f"Failed: {str(e)}", False
            )
            raise

        digital_id = self._lookup_for_operation(auth, "UPDATE_ADDRESS", id_number)

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

        try:
            validate_email(new_email)
        except ValidationError as e:
            self._audit.record(auth.org_name, "UPDATE_EMAIL", id_number, f"Failed: {str(e)}", False)
            raise

        digital_id = self._lookup_for_operation(auth, "UPDATE_EMAIL", id_number)

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
        """Set or clear a restriction flag (used by DVLA-style checks)."""
        try:
            auth.require_permission("update_id")
        except PermissionError as e:
            self._audit.record(auth.org_name, "SET_RESTRICTION", id_number,
                               f"Failed: {str(e)}", False)
            raise

        digital_id = self._lookup_for_operation(auth, "SET_RESTRICTION", id_number)

        if digital_id.status == IDStatus.REVOKED:
            self._audit.record(auth.org_name, "SET_RESTRICTION", id_number,
                               "Failed: Cannot update a revoked ID.", False)
            raise InvalidOperationError("Cannot update a revoked Digital ID.")

        digital_id.has_restriction = has_restriction
        self._audit.record(auth.org_name, "SET_RESTRICTION", id_number,
                           f"Restriction set to {has_restriction}.", True)
        return digital_id

    # Query helpers

    def find_ids_by_name(self, name_pattern: str) -> List[DigitalID]:
        """Case-insensitive substring match on full name."""
        pattern_lower = name_pattern.lower()
        return [d for d in self._identities.values()
                if pattern_lower in d.full_name.lower()]

    def find_ids_by_status(self, status: IDStatus) -> List[DigitalID]:
        return [d for d in self._identities.values() if d.status == status]

    def find_ids_by_nationality(self, nationality: str) -> List[DigitalID]:
        return [d for d in self._identities.values()
                if d.nationality == nationality]

    def get_all_ids(self) -> List[DigitalID]:
        return list(self._identities.values())

    def count_ids(self) -> int:
        return len(self._identities)
