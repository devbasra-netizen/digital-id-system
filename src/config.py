"""Shared settings for permissions and validation limits."""

from src.models.digital_id import OrganisationType

# Maps each organisation type to the operations it is allowed to perform.
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

# Validation constants used by validators.py
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
    """Look up which operations an organisation type is allowed to run."""
    return ORGANISATION_PERMISSIONS.get(org_type, set())
