"""
Platform module — wires together the identity and verification services
over a shared identity store and audit log.
"""

from src.audit.audit_log import AuditLog
from src.services.identity_service import IdentityService
from src.services.verification_service import VerificationService


class DigitalIDPlatform:
    """
    Entry point for the Digital ID system.

    Creates the shared audit log and identity store, then injects them
    into IdentityService (used by the central authority) and
    VerificationService (used by consuming organisations).
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
