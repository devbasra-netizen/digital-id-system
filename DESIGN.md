# Design Notes

Short overview of the main design decisions behind the Digital ID system.

---

## Separation of Identity Management and Verification

The brief says identity management (creation, updates, status changes) and identity consumption (verification, lookup) must be handled separately.  I split these into two service classes:

- **IdentityService** — only the Central Authority uses this.  Handles creating IDs, changing status, and updating mutable fields.
- **VerificationService** — used by consuming organisations (banks, HMRC, DVLA, etc.).  Reads identity data but never modifies it.

Both services share the same in-memory identity store and audit log, wired together by `DigitalIDPlatform`.

---

## Dependency Injection

Services receive their dependencies through constructor parameters rather than creating them internally:

```python
class IdentityService:
    def __init__(self, audit_log: AuditLog) -> None:
        self._identities = {}
        self._audit = audit_log
```

This makes testing straightforward — each test creates a fresh `DigitalIDPlatform` so there's no shared state between tests.

---

## Status Lifecycle

Digital IDs follow a simple state machine:

```
PENDING ──→ ACTIVE ⇄ SUSPENDED ──→ REVOKED (terminal)
```

Key rules:
- Only ACTIVE IDs can be suspended
- Only SUSPENDED IDs can be reinstated
- REVOKED is terminal — no further transitions or updates allowed
- Activating an already-ACTIVE ID is idempotent (no error, no change)
- Revoking an already-REVOKED ID is also idempotent

Each suspension is tracked with a `(start_date, end_date)` tuple so that the tax authority can check whether an ID was suspended during a reporting period.

---

## Custom Exception Hierarchy

I defined a base `DigitalIDError` and four specific exceptions:

```
DigitalIDError (base)
├── ValidationError    (also extends ValueError)
├── InvalidOperationError (also extends ValueError)
├── PermissionError    (also extends builtins.PermissionError)
└── IDNotFoundError    (also extends KeyError)
```

Each one inherits from both `DigitalIDError` and a built-in Python exception.  This means tests can catch either `ValueError` or `DigitalIDError` and both work.  It also means `except PermissionError` in calling code catches both the built-in and custom versions.

---

## Role-Based Access Control

Every organisation is represented by an `OrganisationAuth` object that wraps a type and a name.  The permission matrix lives in `config.py`:

```python
ORGANISATION_PERMISSIONS = {
    OrganisationType.CENTRAL_AUTHORITY: {"create_id", "update_id", "change_status", ...},
    OrganisationType.TAX_AUTHORITY: {"verify_with_history"},
    OrganisationType.BANK: {"verify_basic"},
    ...
}
```

Every service method calls `auth.require_permission(operation)` as its first step.  If the organisation isn't allowed, a `PermissionError` is raised and the failure is recorded in the audit log.

---

## Immutability Enforcement

Some fields on a Digital ID (name, date of birth, nationality) should never change after creation.  Rather than using a frozen dataclass (which would make tests harder to set up), I enforce this at the service layer: there are simply no methods that modify those fields.  The mutable fields (`address`, `email`, `has_restriction`) have dedicated update methods that check permissions and record audit entries.

---

## Audit Trail

The `AuditLog` is append-only.  Every operation — whether it succeeds or fails — gets a timestamped entry with the organisation name, operation type, affected ID, a human-readable detail string, and a success/failure flag.  This supports the brief's requirement that key actions are recorded so system behaviour can be examined.

---

## Input Validation

Six validator functions in `validators.py` check inputs before any data is stored.  All limits (name length, email regex, etc.) are pulled from `SYSTEM_CONSTANTS` in `config.py` so they can be changed in one place.

---

## Configuration Externalisation

All magic numbers and permission rules live in `config.py`.  The services don't hard-code any limits or permission checks — they delegate to the config module and the `OrganisationAuth` class.

