# Digital ID System

Backend system for managing digital identities across a federated ecosystem of organisations.  Built for the **IOT452U** Software Engineering Tools and Techniques coursework.

**GitHub Repository:** https://github.com/YOUR_USERNAME/digital-id-system

---

## How to Run

### Prerequisites

- Python 3.12+
- pip

### Setup

```bash
git clone https://github.com/YOUR_USERNAME/digital-id-system.git
cd digital-id-system
pip install -r requirements.txt
```

### Run the demo

```bash
python main.py
```

This walks through 12 scenarios: creating IDs, lifecycle transitions, three verification modes, permission enforcement, mutable-field updates, and the full audit trail.

### Run the tests

```bash
pytest tests/ -v
```

80 automated tests across four test files.

### Lint

```bash
flake8 src/ --max-line-length=100
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
│   ├── test_identity_service.py   # 23 tests — lifecycle + updates
│   ├── test_verification_service.py # 19 tests — all three modes
│   ├── test_validation.py         # 28 tests — all six validators
│   └── test_audit_log.py          # 10 tests — audit recording + queries
├── main.py                        # Console demonstration
├── DESIGN.md                      # Design decisions and patterns
├── requirements.txt
└── .github/workflows/ci.yml       # GitHub Actions CI
```

---

## Key Features

### Digital ID Lifecycle

```
PENDING ──→ ACTIVE ⇄ SUSPENDED
  Any non-revoked state ──→ REVOKED (terminal)
```

- Immutable fields: `id_number`, `full_name`, `date_of_birth`, `nationality`
- Mutable fields: `address`, `email`, `has_restriction`
- Suspension history tracked with start/end dates

### Role-Based Access Control

Eight organisation types, each with a defined set of allowed operations.  Only the Central Authority can create or modify IDs; other organisations can only verify.

### Three Verification Modes

| Mode | Used by | What it checks |
|------|---------|----------------|
| Basic | Banks, Employers | Is the ID currently ACTIVE? |
| With History | Tax Authority | ACTIVE + not suspended during a reporting period |
| With Restriction | DVLA | ACTIVE + no restriction flag set |

### Audit Trail

Every operation (successful or failed) is recorded in an append-only log with timestamp, organisation, operation type, affected ID, and outcome.

### Input Validation

Six validators enforce data quality at service entry points: ID number, name, email, address, date of birth, nationality.

---

## Testing

80 tests organised into four files:

- **test_identity_service.py** — creation, status transitions, idempotency, updates, permission denial
- **test_verification_service.py** — all three modes across different org types
- **test_validation.py** — happy paths, boundary cases, and invalid inputs for each validator
- **test_audit_log.py** — recording, querying, and filtering audit entries

CI runs automatically on every push via GitHub Actions.

---

## Design Decisions

See [DESIGN.md](DESIGN.md) for notes on dependency injection, the exception hierarchy, immutability enforcement, and the permission model.
