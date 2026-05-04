# Digital ID System

This repo is my IOT452U coursework project. I built a Python backend that stores digital IDs and lets organisations verify them with role-based permissions.

**GitHub Repository:** https://github.com/devbasra-netizen/digital-id-system

---

## Running It

### Prerequisites

- Python 3.12+
- pip

### Setup

```bash
git clone https://github.com/devbasra-netizen/digital-id-system.git
cd digital-id-system
pip install -r requirements.txt
```

### Run the demo

```bash
python main.py
```

The demo walks through 12 scenarios: creating IDs, changing status, running verification checks, hitting permission errors, updating fields, and checking the audit trail.

### Run the tests

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

Tests are split into four files so each area is easier to debug.

### Lint

```bash
flake8 src tests --max-line-length=100
mypy src
```

---

## Project Structure

```
digital-id-system/
├── src/
│   ├── models/
│   │   └── digital_id.py          # DigitalID dataclass + enums
│   ├── auth/
│   │   └── organisation_auth.py   # Role-based permission checks
│   ├── services/
│   │   ├── identity_service.py    # Lifecycle management (central authority)
│   │   └── verification_service.py# Three verification modes (consuming orgs)
│   ├── audit/
│   │   └── audit_log.py           # Append-only audit trail
│   ├── exceptions.py              # Custom exception hierarchy
│   ├── validators.py              # Input validation functions
│   ├── config.py                  # Permission matrix + constants
│   └── platform.py                # Wires services together
├── tests/
│   ├── test_identity_service.py   # Identity lifecycle, updates, and query tests
│   ├── test_verification_service.py # Verification mode and permission tests
│   ├── test_validation.py         # Validator boundary and invalid-input tests
│   └── test_audit_log.py          # Audit recording and query tests
├── main.py                        # Console demonstration
├── DESIGN.md                      # Design decisions and trade-offs
├── requirements.txt
└── .github/workflows/ci.yml       # GitHub Actions CI
```

---

## What the system does

### Digital ID Lifecycle

```
PENDING ──→ ACTIVE ⇄ SUSPENDED
  Any non-revoked state ──→ REVOKED (terminal)
```

- Immutable fields: `id_number`, `full_name`, `date_of_birth`, `nationality`, `created_date`
- Mutable fields: `address`, `email`, `has_restriction`
- Suspension history tracked with start/end dates
- `suspend_id` only accepts `ACTIVE` IDs (re-suspending an already `SUSPENDED` ID raises an error)

### Role-Based Access Control

There are eight organisation types. Only the Central Authority can create or update IDs. Everyone else can verify only.

### Three Verification Modes

| Mode | Used by | What it checks |
|------|---------|----------------|
| Basic | Banks, Employers | Is the ID currently ACTIVE? |
| With History | Tax Authority | ACTIVE + not suspended during a reporting period |
| With Restriction | DVLA | ACTIVE + no restriction flag set |

### Audit Trail

Every operation (success or failure) is written to an append-only audit log with timestamp, organisation, operation, ID, and outcome.

Validation errors and "ID not found" failures are logged too, so rejected requests are still traceable.

### Input Validation

Six validators check the main input fields: ID number, name, email, address, date of birth, and nationality.

---

## Testing

Tests are organised into four files:

- **test_identity_service.py** — creation, status transitions, query methods, overlap boundaries, updates, permission denial
- **test_verification_service.py** — all three modes across different org types
- **test_validation.py** — happy paths, boundary cases, and invalid inputs for each validator
- **test_audit_log.py** — recording, querying, and filtering audit entries

CI runs on each push with GitHub Actions.
The workflow runs `flake8`, `mypy`, and `pytest` with coverage output.

---


## Design notes

I wrote up the design trade-offs in [DESIGN.md](DESIGN.md), including dependency injection, the exception hierarchy, model immutability, and the permission model.
