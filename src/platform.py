"""Wires the two services together over a single audit log and identity store."""

from src.audit.audit_log import AuditLog
from src.services.identity_service import IdentityService
from src.services.verification_service import VerificationService


class DigitalIDPlatform:
    """Top-level handle used by the demo script and the test suite.

    One audit log and one identity store are created here and shared
    between IdentityService and VerificationService, so writes done on
    one side are immediately visible to the other.
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
