# User Stories and Iteration Plan

I worked through the coursework in four iterations. The rule I set for myself
was to keep `main.py` runnable at the end of each one — "keep main green"
rather than leaving things broken between iterations. Stories use the standard
`As a ... I want ... so that ...` format, with acceptance criteria that tie
directly to the tests in `tests/`.

The status column shows where each story ended up at submission.

## Iteration 0 - Project skeleton

| ID | Story | Status |
|---|---|---|
| S0.1 | As a developer, I want a Python project skeleton with a virtualenv, requirements file, and `.gitignore`, so that I can develop locally without leaking caches into Git. | Done |
| S0.2 | As a developer, I want the package layout split into `models`, `services`, `auth`, `audit`, so that responsibilities are obvious from the directory tree. | Done |
| S0.3 | As a developer, I want a custom exception hierarchy under one base class, so that callers can choose between specific or built-in `except` clauses. | Done |

## Iteration 1 - Identity lifecycle

| ID | Story | Acceptance | Status |
|---|---|---|---|
| S1.1 | As the Central Authority, I want to create a Digital ID with the required attributes, so that the platform has a record to manage. | New IDs default to `PENDING`; duplicate `id_number` rejected. | Done |
| S1.2 | As the Central Authority, I want to activate, suspend, reinstate and revoke IDs under defined rules, so that the lifecycle stays consistent. | `PENDING -> ACTIVE`, `ACTIVE <-> SUSPENDED`, `* -> REVOKED` (terminal). | Done |
| S1.3 | As an auditor, I want certain attributes (id number, name, DOB, nationality) to be immutable after creation, so that historical identity data cannot be silently rewritten. | Direct assignment to those fields raises `AttributeError`. | Done |
| S1.4 | As the Central Authority, I want to update mutable attributes (address, email, restriction flag), but not on revoked IDs. | `update_*` and `set_restriction` reject `REVOKED`. | Done |
| S1.5 | As an auditor, I want a suspension history with start/end dates, so that "was this ID suspended at any point in this period" is answerable. | `suspension_history` is `(start, end \| None)` tuples; reinstate closes the open record. | Done |

## Iteration 2 - Verification and authorisation

| ID | Story | Acceptance | Status |
|---|---|---|---|
| S2.1 | As a bank or employer, I want a basic yes/no validity check, so that I can verify an applicant without seeing identity attributes. | `verify_basic` returns valid only when status is `ACTIVE`. | Done |
| S2.2 | As HMRC, I want to verify that an ID was active and not suspended during a reporting period, so that I can trust returns filed for that period. | `verify_with_history` rejects if currently non-active or any suspension overlaps the period. | Done |
| S2.3 | As DVLA, I want to verify that an ID is active and free of any restriction, so that I can issue or renew a licence. | `verify_with_restriction_check` returns false if `has_restriction` is set. | Done |
| S2.4 | As the platform owner, I want every operation to be authorised against an organisation-type permission matrix, so that portals can't perform actions outside their role. | Bank cannot create or update; HMRC cannot use basic verify; DVLA cannot use history; etc. | Done |
| S2.5 | As an auditor, I want every action - including failures - logged with timestamp, org, operation, and outcome, so that misuse is visible after the fact. | `AuditEntry` is frozen; `record(...)` is the only mutation point. | Done |

## Iteration 3 - Validation, edge cases, hardening

| ID | Story | Acceptance | Status |
|---|---|---|---|
| S3.1 | As the Central Authority, I want every input validated before storage (length, format, date sanity), so that invalid data never enters the store. | `validators.py` covers id number, name, email, address, DOB, nationality. | Done |
| S3.2 | As an auditor, I want validation failures, permission denials, and "not found" lookups all written to the audit log with `success=False`, so that abuse patterns are visible. | Tests in `test_identity_service.py` and `test_verification_service.py` assert the failure entries. | Done |
| S3.3 | As a developer, I want the suspension overlap logic covered for boundary cases (open suspensions, exact-day touches, ranges before/after), so that HMRC checks are reliable. | `TestSuspensionOverlapBoundaries` covers these. | Done |
| S3.4 | As a developer, I want a single demo script that exercises every capability end-to-end, so the marker can see behaviour without reading individual tests. | `main.py` walks through all 12 sections cleanly. | Done |

## Iteration 4 - Continuous integration and documentation

| ID | Story | Status |
|---|---|---|
| S4.1 | As a developer, I want CI to run flake8, mypy, and pytest with a 90% coverage gate on every push and PR, so regressions show up immediately. | Done (`.github/workflows/ci.yml`). |
| S4.2 | As a developer, I want a weekly `pip-audit` against `requirements.txt`, so that vulnerable transitive dependencies are flagged. | Done (`.github/workflows/security.yml`). |
| S4.3 | As an assessor, I want a README with run instructions, repo link, and a layout diagram, plus a separate design write-up, so that the code is approachable cold. | Done (`README.md`, `DESIGN.md`). |
| S4.4 | As a developer, I want a release workflow that bundles tagged source as a tarball, so submissions are reproducible. | Done (`.github/workflows/release.yml`). |

## Out of scope

Stuff I decided not to do — reasoning is in `DESIGN.md`:

- **Persistence** — the store is in-memory. The brief says console backend with
  no framework, and SQLite would have added infrastructure the assessment isn't
  asking for.
- **Concurrency / locking** — single-threaded by design.
- **Network / HTTP layer** — the brief is explicit there's no web layer.

## Commit history

I tagged commits with conventional-commit prefixes (`feat:`, `test:`, `fix:`,
`docs:`, `refactor:`, `chore:`, `ci:`). `git log --oneline` should map fairly
neatly onto the iteration headings above.
