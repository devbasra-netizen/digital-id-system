# Design Notes

Main design choices and why I made them.
The brief separates identity *management* from identity *consumption*, so most
of the structure here comes from taking that seriously.

## 1. Two services, one shared store

I split the logic across two services:

- `IdentityService` — everything the central authority does
  (create, update, change status).
- `VerificationService` — everything consuming organisations do
  (the three verification modes).

`DigitalIDPlatform` wires both services to the same in-memory store and the
same audit log. Read and write paths are conceptually separate, but they talk
to the same underlying data. It's loosely CQRS-flavoured, not a traditional
layered design.

I did consider a single `DigitalIDService`, but the brief is pretty clear that
management and consumption "must be handled separately", so the split felt like
the right call.

## 2. Dependency injection over module globals

Both services receive their `AuditLog` (and the identity store, in
verification's case) through their constructors — no global registry, no
singleton.

Two reasons:
1. Tests spin up a fresh `DigitalIDPlatform()` per fixture and there's no
   shared state to worry about.
2. Each class's dependencies are visible from its signature, which makes things
   easier to follow.

## 3. Status lifecycle

```
PENDING -> ACTIVE <-> SUSPENDED
any non-revoked state -> REVOKED   (terminal)
```

Rules enforced in the service layer:

- `suspend_id` only accepts `ACTIVE` IDs.
- `activate_id` is idempotent if the ID is already `ACTIVE`.
- `revoke_id` is idempotent if already `REVOKED`.
- Once `REVOKED`, no further status changes or attribute updates are allowed.

Suspension periods are `(start_date, end_date | None)` tuples. A `None` end
means the suspension is still open. That makes the overlap check in
`was_suspended_during(...)` straightforward and keeps the history queryable for
HMRC-style reporting.

## 4. Exception hierarchy

There's a base `DigitalIDError` with subclasses for validation, invalid
operations, permissions, and missing IDs. Each one also inherits from a related
Python built-in (`ValueError`, `PermissionError`, `KeyError`).

The dual inheritance means callers can catch the project-specific class if they
want precision, or fall back on the broad built-in if they don't care about the
distinction. I find that tidier than forcing callers to learn a new exception
vocabulary from scratch.

## 5. Permission model

Per-organisation permissions live in a dictionary in `config.py`. The
`OrganisationAuth` wrapper exposes `can_perform(...)` and
`require_permission(...)`. Every service method calls `require_permission` first,
and a denial both raises `PermissionError` *and* writes a failure entry to the
audit log.

Failed auth attempts are exactly the kind of thing an auditor cares about, so
silently dropping them would miss the point.

## 6. Immutability of core identity fields

Five fields are locked once the record is created:

- `id_number`
- `full_name`
- `date_of_birth`
- `nationality`
- `created_date`

I did this with a custom `__setattr__` on `DigitalID` rather than freezing the
whole dataclass, because some lifecycle fields (`status`, `suspension_history`,
`address`, `email`, `has_restriction`) genuinely need to mutate. A
`_is_initialized` flag flips on at the end of `__post_init__`, and after that
any write to an immutable field raises `AttributeError`.

Catches programmer errors at the point they happen, rather than letting them
silently corrupt a record.

## 7. Audit log

`AuditLog` is append-only — no `delete` or `update`, and `AuditEntry` is a
frozen dataclass so records can't be edited after the fact. Every operation
(including failures) writes an entry with:

- timestamp
- organisation name
- operation
- ID number
- a short details string
- success / failure flag

The query helpers (`get_failed_entries`, `get_entries_by_organisation`, etc.)
are read-only views over the internal list.

## 8. Validation and config

All input validation happens in `validators.py` before anything is written to
the store. Length limits and the email regex live in a single `SYSTEM_CONSTANTS`
dictionary in `config.py` so the rules are in one place.

`verify_with_history(...)` also validates its date range first: dates must be
`date` objects and `start <= end`. A bad range gets a `ValidationError` and a
failure entry in the audit log.

## 9. What I left out

- **Persistence.** The brief says console-based backend, no UI or framework,
  so in-memory is fine for this scope. SQLite would have added infrastructure
  concerns that aren't being assessed.
- **Concurrency.** Single-threaded, single-process. Locks would have
  complicated the lifecycle logic for no benefit here.
- **A network layer.** The brief explicitly says no web layer.

The core architecture (DI, two services over a shared store, audit log as a
proper collaborator) would still hold up if any of these were added later.
