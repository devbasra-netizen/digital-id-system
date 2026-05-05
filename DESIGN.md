# Design Notes

This file explains the main design choices I made for the coursework.

## 1) Two services instead of one

I split the logic into:

- `IdentityService` for Central Authority actions (create/update/change status)
- `VerificationService` for organisations that only need to check IDs

This matches the brief and keeps write actions separate from read/verify actions.

Both services are connected by `DigitalIDPlatform`, which gives them the same in-memory ID store and the same audit log.

## 2) Dependency injection for easier testing

I pass shared objects (like `AuditLog`) into service constructors instead of creating them inside each method.

Why I did this:

- tests can build a fresh platform each time
- no hidden global state
- easier to reason about what each service depends on

## 3) Status lifecycle rules

The ID status flow is:

```text
PENDING -> ACTIVE <-> SUSPENDED -> REVOKED (final)
```

Rules implemented in service methods:

- only `ACTIVE` IDs can be suspended
- only `SUSPENDED` IDs can be reinstated
- `REVOKED` is terminal (no more status changes or field updates)
- suspend on already suspended ID raises `InvalidOperationError`
- activate/revoke on same current state is idempotent

I store suspension periods as `(start_date, end_date)` tuples so history checks can test overlap with a date range.

## 4) Exception structure

I used a base `DigitalIDError`, then specific exceptions for validation, invalid operations, permissions, and missing IDs.

Each one also inherits from a related Python built-in exception (`ValueError`, `PermissionError`, `KeyError`).

That means callers can either catch project-specific exceptions or broad built-in types.

## 5) Permission model

Permissions are based on organisation type and are defined in `config.py`.

Each service method checks permissions first with `auth.require_permission(...)`. If not allowed:

- raise `PermissionError`
- write a failed entry to the audit log

So denied requests are still visible in logs.

## 6) Data immutability

Core identity fields are locked after creation:

- `id_number`
- `full_name`
- `date_of_birth`
- `nationality`
- `created_date`

Other fields (`address`, `email`, `status`, `has_restriction`, `suspension_history`) can change, but only through service methods, so checks + logging always happen.

I used a `__setattr__` guard in `DigitalID` instead of freezing the whole dataclass because some lifecycle fields must still update.

## 7) Audit logging

`AuditLog` is append-only.

Every action writes:

- timestamp
- organisation
- operation name
- ID number
- details
- success/failure

`AuditEntry` is frozen, so old entries cannot be edited.

## 8) Validation and config

Input validation happens before data is stored (`validators.py`).

Limits and regex rules are kept in `SYSTEM_CONSTANTS` inside `config.py`, so I do not hard-code values across multiple files.

For `verify_with_history(...)`, the date range is also validated (`start <= end`, proper `date` values).

