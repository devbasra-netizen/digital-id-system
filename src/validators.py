"""Validation helpers run before any ID data is stored."""

import re
from datetime import date
from src.exceptions import ValidationError
from src.config import SYSTEM_CONSTANTS


def validate_id_number(id_number: str) -> None:
    """ID number must be a non-empty string up to 50 chars."""
    if not id_number or not isinstance(id_number, str):
        raise ValidationError("ID number cannot be empty or null.")
    if len(id_number.strip()) == 0:
        raise ValidationError("ID number cannot be blank.")
    if len(id_number) > 50:
        raise ValidationError("ID number cannot exceed 50 characters.")


def validate_name(name: str, field_name: str = "Name") -> None:
    """Name must be within configured min/max length."""
    if not name or not isinstance(name, str):
        raise ValidationError(f"{field_name} cannot be empty or null.")
    if len(name.strip()) == 0:
        raise ValidationError(f"{field_name} cannot be blank.")

    min_len = int(SYSTEM_CONSTANTS["MIN_NAME_LENGTH"])
    max_len = int(SYSTEM_CONSTANTS["MAX_NAME_LENGTH"])

    if len(name) < min_len:
        raise ValidationError(f"{field_name} must be at least {min_len} characters.")
    if len(name) > max_len:
        raise ValidationError(f"{field_name} cannot exceed {max_len} characters.")


def validate_email(email: str) -> None:
    """Email must match the regex in SYSTEM_CONSTANTS."""
    if not email or not isinstance(email, str):
        raise ValidationError("Email cannot be empty or null.")
    if len(email.strip()) == 0:
        raise ValidationError("Email cannot be blank.")

    email_regex = str(SYSTEM_CONSTANTS["EMAIL_REGEX"])
    if not re.match(email_regex, email):
        raise ValidationError(f"Email '{email}' is not in a valid format.")


def validate_address(address: str) -> None:
    """Address must be within configured min/max length."""
    if not address or not isinstance(address, str):
        raise ValidationError("Address cannot be empty or null.")
    if len(address.strip()) == 0:
        raise ValidationError("Address cannot be blank.")

    min_len = int(SYSTEM_CONSTANTS["MIN_ADDRESS_LENGTH"])
    max_len = int(SYSTEM_CONSTANTS["MAX_ADDRESS_LENGTH"])

    if len(address) < min_len:
        raise ValidationError(f"Address must be at least {min_len} characters.")
    if len(address) > max_len:
        raise ValidationError(f"Address cannot exceed {max_len} characters.")


def validate_date_of_birth(date_of_birth: date) -> None:
    """DOB must be a date, not in the future, and in allowed age range."""
    if not isinstance(date_of_birth, date):
        raise ValidationError("Date of birth must be a valid date object.")

    today = date.today()

    if date_of_birth > today:
        raise ValidationError("Date of birth cannot be in the future.")

    min_year = int(SYSTEM_CONSTANTS["MIN_YEAR_OF_BIRTH"])
    if date_of_birth.year < min_year:
        raise ValidationError(f"Date of birth cannot be before year {min_year}.")

    max_age = int(SYSTEM_CONSTANTS["MAX_AGE_YEARS"])
    age = today.year - date_of_birth.year
    if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
        age -= 1

    if age > max_age:
        raise ValidationError(f"Age cannot exceed {max_age} years.")


def validate_nationality(nationality: str) -> None:
    """Nationality must be a non-empty string up to 100 chars."""
    if not nationality or not isinstance(nationality, str):
        raise ValidationError("Nationality cannot be empty or null.")
    if len(nationality.strip()) == 0:
        raise ValidationError("Nationality cannot be blank.")
    if len(nationality) > 100:
        raise ValidationError("Nationality cannot exceed 100 characters.")
