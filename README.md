# Digital ID System

IOT452U coursework. A console-based backend in Python that models a
federated digital ID platform: a single central authority manages the
identities, and other organisations (HMRC, DVLA, banks, employers,
welfare, etc.) verify them through role-specific operations.

GitHub: https://github.com/devbasra-netizen/digital-id-system

## Running it

You need Python 3.12+ and pip.

```bash
git clone https://github.com/devbasra-netizen/digital-id-system.git
cd digital-id-system
pip install -r requirements.txt
```

Run the demo, which walks through every capability end-to-end:

```bash
python main.py
```

Run the test suite (pytest, coverage report goes to the terminal):

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

Lint and type checks (optional, but they're part of CI):

```bash
flake8 src tests --max-line-length=100
mypy src
```

## Layout

```
digital-id-system/
├── src/
│   ├── models/digital_id.py         # DigitalID dataclass, IDStatus, OrganisationType
│   ├── auth/organisation_auth.py    # Permission wrapper for callers
│   ├── services/
│   │   ├── identity_service.py      # Lifecycle: create / update / status changes
│   │   └── verification_service.py  # The three verification modes
│   ├── audit/audit_log.py           # Append-only audit trail
│   ├── exceptions.py                # Custom exception hierarchy
│   ├── validators.py                # Input validation helpers
│   ├── config.py                    # Permission matrix + validation limits
│   └── platform.py                  # Wires the services together
├── tests/                           # pytest suite (~115 tests)
├── .github/workflows/               # CI, security audit, release bundle
├── main.py                          # Console demo
├── DESIGN.md                        # Design rationale
├── USER_STORIES.md                  # Backlog and per-iteration delivery
└── requirements.txt
```

## How the system behaves

### Lifecycle

```
PENDING -> ACTIVE <-> SUSPENDED
any non-revoked state -> REVOKED   (terminal)
```

- Immutable after creation: `id_number`, `full_name`, `date_of_birth`,
  `nationality`, `created_date`.
- Mutable through `IdentityService` only: `address`, `email`, `status`,
  `has_restriction`, `suspension_history`.
- Suspensions are stored as `(start, end | None)` tuples so the history
  is queryable for reporting periods.

### Who can do what

`config.py` holds the permission matrix. Every service method calls
`auth.require_permission(...)` first; a denial raises `PermissionError`
and writes a failure entry to the audit log.

| Role | Allowed |
|---|---|
| Central Authority | create, update, change status, all verify modes |
| Tax Authority (HMRC) | `verify_with_history` |
| Driving Licence Authority (DVLA) | `verify_with_restriction` |
| Bank, Employer, Welfare, Local Authority | `verify_basic` |
| Immigration | `verify_basic`, `verify_with_history` |

### Verification modes

- `verify_basic` - is this ID currently `ACTIVE`? Yes/no.
- `verify_with_history` - active *and* not suspended at any point during
  a given reporting period.
- `verify_with_restriction_check` - active *and* no restriction flag set.

### Audit log

Every action (success or failure) is appended to a frozen `AuditEntry`
with timestamp, organisation, operation, ID number, details, and a
success flag. The log itself only exposes append + query helpers, so
historical entries cannot be edited or deleted.

## Tests

```
tests/test_identity_service.py     - lifecycle, updates, queries, audit hooks
tests/test_verification_service.py - the three verification modes
tests/test_validation.py           - validator edge cases
tests/test_audit_log.py            - audit recording, querying, immutability
```

CI (`.github/workflows/ci.yml`) runs flake8, mypy, and pytest on every
push and pull request, against Python 3.11 and 3.12, with a 90%
coverage gate. There's also a weekly `pip-audit` security scan and a
release-bundle workflow that produces a tarball on tag push.

## Design write-up

Longer-form rationale (why two services, why the immutability guard,
exception hierarchy choices, what was deliberately left out) is in
[DESIGN.md](DESIGN.md). The development backlog and per-iteration
delivery is in [USER_STORIES.md](USER_STORIES.md).
