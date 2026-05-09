# Design Notes

These are the main design choices I made and the reasoning behind them.
The brief explicitly separates identity *management* from identity
*consumption*, so most of the structure here falls out of taking that
distinction seriously.

## 1. Two services, one shared store

I split the logic into two services rather than one:

- `IdentityService` - everything the central authority does
  (create, update, change status).
- `VerificationService` - everything consuming organisations do
  (the three verification modes).

`DigitalIDPlatform` constructs both services and hands them the same
in-memory identity store and the same audit log. That keeps the read and
write paths conceptually separate while still operating on the same
underlying data, which is closer in spirit to a CQRS-style split than
to a traditional layered design.

I considered putting it all behind a single `DigitalIDService`, but the
brief is firm that "identity management ... and identity consumption ...
must be handled separately by the system", so the split was the right
call.

## 2. Dependency injection over module globals

Both services receive their `AuditLog` (and the identity store, in the
case of verification) through their constructors. There is no global
registry and no singleton.

Two reasons:
1. Tests can spin up a brand-new platform per test (`DigitalIDPlatform()`
   in a fixture) and not worry about state leaking across cases.
2. It makes the dependencies of each class obvious from its signature.

## 3. Status lifecycle

```
PENDING -> ACTIVE <-> SUSPENDED
any non-revoked state -> REVOKED   (terminal)
```

Rules implemented in the service layer:

- `suspend_id` only accepts `ACTIVE` IDs.
- `activate_id` is idempotent if the ID is already `ACTIVE`.
- `revoke_id` is idempotent if the ID is already `REVOKED`.
- Once `REVOKED`, no further status changes or attribute updates are accepted.

Suspension periods are stored as `(start_date, end_date | None)` tuples.
A `None` end means the suspension is still open. That representation
makes the overlap check in `was_suspended_during(...)` straightforward
and keeps the history queryable for HMRC-style reporting.

## 4. Exception hierarchy

There is a base `DigitalIDError`, with specific subclasses for
validation, invalid operations, permissions, and missing IDs. Each one
also inherits from a related Python built-in (`ValueError`,
`PermissionError`, `KeyError`).

That dual inheritance means callers have a choice: catch the
project-specific class for precise handling, or fall back on the broad
built-in if they don't need the distinction. I find it tidier than
forcing every caller to learn a parallel exception vocabulary.

## 5. Permission model

Per-organisation permissions live in a dictionary in `config.py`. The
`OrganisationAuth` wrapper exposes `can_perform(...)` and
`require_permission(...)`. Every service method calls
`require_permission` before doing anything else, and a denial both
raises `PermissionError` *and* writes a failure entry to the audit log.

Failed authorisation attempts are part of the trail an auditor would
care about, so silently rejecting them would defeat the point of the
audit log.

## 6. Immutability of core identity fields

Five fields are locked once the record is constructed:

- `id_number`
- `full_name`
- `date_of_birth`
- `nationality`
- `created_date`

I implemented this with a custom `__setattr__` on `DigitalID` rather
than freezing the whole dataclass, because some lifecycle fields
(`status`, `suspension_history`, `address`, `email`,
`has_restriction`) genuinely have to mutate. A `_is_initialized` flag
flips on at the end of `__post_init__`, after which writes to immutable
fields raise `AttributeError`.

This catches programmer errors at the point they happen instead of
quietly corrupting an identity record.

## 7. Audit log

`AuditLog` is append-only - there is no `delete` or `update` method,
and `AuditEntry` is a frozen dataclass so individual records can't be
edited after the fact. Every operation, including failed ones, writes
an entry containing:

- timestamp
- organisation name
- operation
- ID number
- a short details string
- success / failure flag

The query helpers (`get_failed_entries`,
`get_entries_by_organisation`, etc.) are read-only views over the
internal list.

## 8. Validation and config

All input validation happens in `validators.py` *before* anything is
written to the store. Length limits and the email regex live in a
single `SYSTEM_CONSTANTS` dictionary in `config.py` so the rules are in
one place rather than scattered across modules.

`verify_with_history(...)` also validates its date range before doing
the lookup: dates must be `date` objects and `start <= end`. A bad
range is rejected with a `ValidationError` and recorded as a failure in
the audit log.

## 9. What I deliberately left out

- **Persistence.** The brief says console-based backend, no UI or
  framework, so the in-memory store is appropriate for the scope.
  Adding SQLite would bring infrastructure concerns the assessment is
  not asking about.
- **Concurrency.** Single-threaded, single-process. The brief does not
  require it and adding locks would obscure the lifecycle logic.
- **A network layer.** Same reason - the brief explicitly says no web
  layer.

The architecture (DI, two services over a shared store, audit log as a
collaborator rather than a side effect) would still hold up if any of
these were added later.
