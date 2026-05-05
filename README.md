# Digital ID System

This is my IOT452U coursework project. I built it in Python to model a digital ID platform where one central authority manages IDs and other organisations verify them.

## Quick start

### What you need

- Python 3.12+
- pip

### Install

```bash
git clone https://github.com/devbasra-netizen/digital-id-system.git
cd digital-id-system
pip install -r requirements.txt
```

### Run demo script

```bash
python main.py
```

The script runs through creation, status changes, verification checks, permission failures, updates, and audit log output.

### Run tests

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

### Optional lint/type checks

```bash
flake8 src tests --max-line-length=100
mypy src
```

## Project layout

```text
digital-id-system/
├── src/
│   ├── models/digital_id.py
│   ├── auth/organisation_auth.py
│   ├── services/identity_service.py
│   ├── services/verification_service.py
│   ├── audit/audit_log.py
│   ├── exceptions.py
│   ├── validators.py
│   ├── config.py
│   └── platform.py
├── tests/
├── main.py
├── DESIGN.md
└── requirements.txt
```

## Main behaviour

### ID lifecycle

```text
PENDING -> ACTIVE <-> SUSPENDED
any non-revoked state -> REVOKED (final)
```

- Immutable fields: `id_number`, `full_name`, `date_of_birth`, `nationality`, `created_date`
- Mutable fields: `address`, `email`, `has_restriction`
- Suspension history stores start/end dates

### Organisation permissions

- Central Authority can create, update, and change status
- Other organisation types can verify based on their allowed mode

### Verification modes

- `verify_basic`: checks if ID is currently `ACTIVE`
- `verify_with_history`: checks active status and suspension overlap in a date range
- `verify_with_restriction_check`: checks active status and restriction flag

### Audit logging

Every request is logged as success/failure with timestamp, organisation, operation, ID, and details.

## Testing notes

- `tests/test_identity_service.py`: lifecycle, updates, searching, permission checks
- `tests/test_verification_service.py`: verification rules by organisation type
- `tests/test_validation.py`: validator limits and invalid inputs
- `tests/test_audit_log.py`: audit entry recording and filtering

## Design write-up

More detail on decisions and trade-offs is in `DESIGN.md`.
