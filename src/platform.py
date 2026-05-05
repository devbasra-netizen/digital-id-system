"""Builds the platform object and links shared services together."""

from src.audit.audit_log import AuditLog
from src.services.identity_service import IdentityService
from src.services.verification_service import VerificationService


class DigitalIDPlatform:
    """Main entry point used by tests and the demo script.

    This class creates one audit log and one identity store, then gives both
    to the identity and verification services.
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
