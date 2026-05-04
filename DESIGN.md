# Design Notes

These are the main decisions I made while building the Digital ID system for coursework.

---

## Splitting management and verification

The brief asks for management and consumption to be separate, so I used two services:

- **IdentityService** - only for the Central Authority. It creates IDs, changes status, and updates mutable fields.
- **VerificationService** - used by consuming organisations (banks, HMRC, DVLA, etc.). It can read and verify data but not change it.

Both services share one in-memory store and one audit log through `DigitalIDPlatform`.

---

## Dependency injection

Services receive their dependencies through constructor parameters rather than creating them internally:

```python
class IdentityService:
    def __init__(self, audit_log: AuditLog) -> None:
        self._identities = {}
        self._audit = audit_log
```

This makes testing easier because each test can create a fresh `DigitalIDPlatform` with no leftover state.

---

## Status lifecycle

Digital IDs follow this state machine:

```
PENDING ──→ ACTIVE ⇄ SUSPENDED ──→ REVOKED (terminal)
```

Rules I enforced:
- Only ACTIVE IDs can be suspended
- Only SUSPENDED IDs can be reinstated
- REVOKED is terminal - no further transitions or updates are allowed
- Suspending an already-SUSPENDED ID raises `InvalidOperationError` (not idempotent)
- Activating an already-ACTIVE ID is idempotent (no error, no change)
- Revoking an already-REVOKED ID is also idempotent

Each suspension is stored as `(start_date, end_date)` so HMRC checks can tell if a suspension overlapped a reporting period.

---

## Custom exception hierarchy

I defined a base `DigitalIDError` and four specific exceptions:

```
DigitalIDError (base)
├── ValidationError    (also extends ValueError)
├── InvalidOperationError (also extends ValueError)
├── PermissionError    (also extends builtins.PermissionError)
└── IDNotFoundError    (also extends KeyError)
```

Each custom exception inherits from both `DigitalIDError` and a related built-in exception. So code can catch either the project-specific error or the usual Python type.

---

## Role-based access control

Each organisation is represented by an `OrganisationAuth` object containing a type and name. The permission matrix lives in `config.py`:

```python
ORGANISATION_PERMISSIONS = {
    OrganisationType.CENTRAL_AUTHORITY: {"create_id", "update_id", "change_status", ...},
    OrganisationType.TAX_AUTHORITY: {"verify_with_history"},
    OrganisationType.BANK: {"verify_basic"},
    ...
}
```

Each service method calls `auth.require_permission(operation)` first. If access is denied, it raises `PermissionError` and also writes the failure to the audit log.

---

## Immutability enforcement

Core identity fields are immutable in `DigitalID` by blocking reassignment after creation. This still protects the data even if someone tries to bypass service methods.

Immutable fields: `id_number`, `full_name`, `date_of_birth`, `nationality`, `created_date`.

Mutable fields (`address`, `email`, `status`, `has_restriction`, `suspension_history`) are still changed by service methods so that permission checks and audit entries stay in one place.

I used a lightweight `__setattr__` guard instead of a fully frozen dataclass because lifecycle fields still need to change.

---

## Audit trail

`AuditLog` is append-only. Every operation (successful or failed) writes a timestamped entry with organisation, operation, affected ID, details, and success flag. That gives traceability required in the brief.

Each `AuditEntry` is immutable (`@dataclass(frozen=True)`), so log entries cannot be edited after they are recorded.

---

## Input validation

Six validator functions in `validators.py` check inputs before anything is stored. Limits (name length, email regex, and so on) live in `SYSTEM_CONSTANTS` in `config.py`.

For tax-history checks, `VerificationService.verify_with_history(...)` also validates the period (`start <= end` and both values are `date` objects).

---

## Configuration externalisation

Constants and permission rules live in `config.py`. Services avoid hard-coded limits and rely on config plus `OrganisationAuth`.

