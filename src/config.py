"""Permission matrix and validation limits.

Keeping these in one place avoids hard-coding magic values across the
service modules and makes the rules easy to inspect.
"""

from src.models.digital_id import OrganisationType


# What each organisation type is allowed to do. Anything not listed is denied.
ORGANISATION_PERMISSIONS: dict[OrganisationType, set[str]] = {
    OrganisationType.CENTRAL_AUTHORITY: {
        "create_id", "update_id", "change_status",
        "verify_basic", "verify_with_history", "verify_with_restriction",
    },
    OrganisationType.TAX_AUTHORITY: {"verify_with_history"},
    OrganisationType.DRIVING_LICENCE_AUTHORITY: {"verify_with_restriction"},
    OrganisationType.EMPLOYER: {"verify_basic"},
    OrganisationType.BANK: {"verify_basic"},
    OrganisationType.WELFARE_SERVICE: {"verify_basic"},
    OrganisationType.LOCAL_AUTHORITY: {"verify_basic"},
    OrganisationType.IMMIGRATION: {"verify_basic", "verify_with_history"},
}


# Validation constants used by validators.py.
SYSTEM_CONSTANTS: dict[str, int | str] = {
    "MIN_YEAR_OF_BIRTH": 1900,
    "MAX_AGE_YEARS": 150,
    "EMAIL_REGEX": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "MIN_ADDRESS_LENGTH": 3,
    "MAX_ADDRESS_LENGTH": 255,
    "MIN_NAME_LENGTH": 2,
    "MAX_NAME_LENGTH": 100,
}


def get_permissions(org_type: OrganisationType) -> set[str]:
    """Return the set of operations an organisation type may perform."""
    return ORGANISATION_PERMISSIONS.get(org_type, set())
