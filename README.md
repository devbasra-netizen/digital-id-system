# Digital ID System

IOT452U coursework. Console-based Python backend for a federated digital ID
platform — a central authority manages identities, other organisations (HMRC,
DVLA, banks, etc.) verify them through role-specific operations.

GitHub: https://github.com/devbasra-netizen/digital-id-system

## Running it

Requires Python 3.12+ and pip.

```bash
git clone https://github.com/devbasra-netizen/digital-id-system.git
cd digital-id-system
pip install -r requirements.txt
```

Demo (walks through every capability):

```bash
python main.py
```

Tests:

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
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

## Tests

Four test modules covering lifecycle, verification, validation edge cases, and
audit log immutability. CI (`.github/workflows/ci.yml`) runs flake8, mypy, and
pytest against Python 3.11 and 3.12 with a 90% coverage gate on every push.

## Design write-up

See [DESIGN.md](DESIGN.md) for the main design decisions and [USER_STORIES.md](USER_STORIES.md)
for the per-iteration backlog.
