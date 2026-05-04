"""Wires the services together using one shared store and one audit log."""

from src.audit.audit_log import AuditLog
from src.services.identity_service import IdentityService
from src.services.verification_service import VerificationService


class DigitalIDPlatform:
    """Main entry point for the Digital ID system.

    It creates the shared audit log and identity store, then passes them to
    IdentityService and VerificationService.
    """

    def __init__(self) -> None:
        self._audit = AuditLog()
        self._identity_service = IdentityService(self._audit)
        self._verification_service = VerificationService(
            self._identity_service.identities,
            self._audit,
        )

    @property
    def identity(self) -> IdentityService:
        return self._identity_service

    @property
    def verification(self) -> VerificationService:
        return self._verification_service

    @property
    def audit(self) -> AuditLog:
        return self._audit
