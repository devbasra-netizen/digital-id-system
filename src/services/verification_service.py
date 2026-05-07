"""Verification Service: read-only checks for consuming organisations.

This service does not modify identity data. It exposes three verification
modes that match the scenarios described in the brief:

    verify_basic                  - banks / employers (yes/no only)
    verify_with_history           - tax authority (suspension period check)
    verify_with_restriction_check - DVLA (status + restriction flag)
"""

from datetime import date
from dataclasses import dataclass
from typing import Dict
from src.models.digital_id import DigitalID, IDStatus
from src.auth.organisation_auth import OrganisationAuth
from src.audit.audit_log import AuditLog
from src.exceptions import IDNotFoundError, PermissionError, ValidationError


@dataclass(frozen=True)
class VerificationResult:
    """Outcome of a verification call: valid/invalid plus a short reason."""

    is_valid: bool
    message: str

    def __repr__(self) -> str:
        status = "VALID" if self.is_valid else "INVALID"
        return f"VerificationResult({status}: {self.message})"


class VerificationService:
    """Three verification modes, all read-only and audit-logged."""

    def __init__(self, identities: Dict[str, DigitalID], audit_log: AuditLog) -> None:
        self._identities: Dict[str, DigitalID] = identities
        self._audit: AuditLog = audit_log

    def _lookup(self, id_number: str) -> DigitalID:
        if id_number not in self._identities:
            raise IDNotFoundError(f"Digital ID '{id_number}' not found.")
        return self._identities[id_number]

    def _validate_period(
        self,
        auth: OrganisationAuth,
        id_number: str,
        period_start: date,
        period_end: date,
    ) -> None:
        """Reject malformed reporting periods before doing any lookup."""
        if not isinstance(period_start, date) or not isinstance(period_end, date):
            message = "Reporting period dates must be date objects."
            self._audit.record(auth.org_name, "VERIFY_WITH_HISTORY", id_number, message, False)
            raise ValidationError(message)

        if period_start > period_end:
            message = "Reporting period start date cannot be after end date."
            self._audit.record(auth.org_name, "VERIFY_WITH_HISTORY", id_number, message, False)
            raise ValidationError(message)

    def verify_basic(self, auth: OrganisationAuth, id_number: str) -> VerificationResult:
        """Valid only if the ID exists and is currently ACTIVE."""
        try:
            auth.require_permission("verify_basic")
        except PermissionError as e:
            self._audit.record(auth.org_name, "VERIFY_BASIC", id_number,
                               f"Unauthorized: {str(e)}", False)
            raise

        try:
            digital_id = self._lookup(id_number)
        except IDNotFoundError:
            self._audit.record(auth.org_name, "VERIFY_BASIC", id_number, "Not found.", False)
            return VerificationResult(False, "Digital ID not found.")

        is_valid = digital_id.status == IDStatus.ACTIVE
        message = f"Status: {digital_id.status.value}"
        self._audit.record(auth.org_name, "VERIFY_BASIC", id_number, message, is_valid)
        return VerificationResult(is_valid, message)

    def verify_with_history(
        self,
        auth: OrganisationAuth,
        id_number: str,
        period_start: date,
        period_end: date,
    ) -> VerificationResult:
        """ID must be ACTIVE and not have been suspended at any point in the period."""
        try:
            auth.require_permission("verify_with_history")
        except PermissionError as e:
            self._audit.record(auth.org_name, "VERIFY_WITH_HISTORY", id_number,
                               f"Unauthorized: {str(e)}", False)
            raise

        self._validate_period(auth, id_number, period_start, period_end)

        try:
            digital_id = self._lookup(id_number)
        except IDNotFoundError:
            self._audit.record(auth.org_name, "VERIFY_WITH_HISTORY", id_number,
                               "Not found.", False)
            return VerificationResult(False, "Digital ID not found.")

        if digital_id.status != IDStatus.ACTIVE:
            message = f"ID is not active. Status: {digital_id.status.value}"
            self._audit.record(auth.org_name, "VERIFY_WITH_HISTORY", id_number, message, False)
            return VerificationResult(False, message)

        if digital_id.was_suspended_during(period_start, period_end):
            message = "ID was suspended during the requested reporting period."
            self._audit.record(auth.org_name, "VERIFY_WITH_HISTORY", id_number, message, False)
            return VerificationResult(False, message)

        message = "ID is active and was not suspended during the requested period."
        self._audit.record(auth.org_name, "VERIFY_WITH_HISTORY", id_number, message, True)
        return VerificationResult(True, message)

    def verify_with_restriction_check(
        self, auth: OrganisationAuth, id_number: str
    ) -> VerificationResult:
        """ID must be ACTIVE and have no restriction flag set."""
        try:
            auth.require_permission("verify_with_restriction")
        except PermissionError as e:
            self._audit.record(auth.org_name, "VERIFY_WITH_RESTRICTION", id_number,
                               f"Unauthorized: {str(e)}", False)
            raise

        try:
            digital_id = self._lookup(id_number)
        except IDNotFoundError:
            self._audit.record(auth.org_name, "VERIFY_WITH_RESTRICTION", id_number,
                               "Not found.", False)
            return VerificationResult(False, "Digital ID not found.")

        if digital_id.status != IDStatus.ACTIVE:
            message = f"ID is not active. Status: {digital_id.status.value}"
            self._audit.record(auth.org_name, "VERIFY_WITH_RESTRICTION", id_number, message, False)
            return VerificationResult(False, message)

        if digital_id.has_restriction:
            message = "ID is active but has a restriction flag; eligibility conditions not met."
            self._audit.record(auth.org_name, "VERIFY_WITH_RESTRICTION", id_number, message, False)
            return VerificationResult(False, message)

        message = "ID is active with no restrictions; eligibility confirmed."
        self._audit.record(auth.org_name, "VERIFY_WITH_RESTRICTION", id_number, message, True)
        return VerificationResult(True, message)
