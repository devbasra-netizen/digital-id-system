"""
Test coverage for input validation module.
Tests the validation functions to ensure data quality enforcement.
"""

import pytest
from datetime import date
from src.validators import (
    validate_id_number, validate_name, validate_email, validate_address,
    validate_date_of_birth, validate_nationality
)
from src.exceptions import ValidationError


class TestIDNumberValidation:
    """Tests for ID number validation."""

    def test_valid_id_number(self):
        """Valid ID numbers should not raise errors."""
        validate_id_number("ID001")
        validate_id_number("ABC-123-XYZ")
        validate_id_number("12345")

    def test_empty_id_number(self):
        """Empty ID number should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_id_number("")

    def test_null_id_number(self):
        """None ID number should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_id_number(None)

    def test_whitespace_only_id(self):
        """Whitespace-only ID should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_id_number("   ")


class TestNameValidation:
    """Tests for name validation."""

    def test_valid_name(self):
        """Valid names should not raise errors."""
        validate_name("John Smith")
        validate_name("Mary O'Brien")
        validate_name("José García")

    def test_name_too_short(self):
        """Names shorter than minimum length should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_name("A")

    def test_name_too_long(self):
        """Names longer than maximum length should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_name("A" * 101)

    def test_empty_name(self):
        """Empty names should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_name("")

    def test_null_name(self):
        """None name should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_name(None)


class TestEmailValidation:
    """Tests for email format validation."""

    def test_valid_emails(self):
        """Valid email addresses should not raise errors."""
        validate_email("user@example.com")
        validate_email("john.smith@company.co.uk")
        validate_email("mary+tag@domain.org")

    def test_invalid_email_formats(self):
        """Invalid email formats should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_email("notanemail")

        with pytest.raises(ValidationError):
            validate_email("@example.com")

        with pytest.raises(ValidationError):
            validate_email("user@")

        with pytest.raises(ValidationError):
            validate_email("user @example.com")

    def test_empty_email(self):
        """Empty emails should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_email("")

    def test_null_email(self):
        """None email should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_email(None)


class TestAddressValidation:
    """Tests for address validation."""

    def test_valid_addresses(self):
        """Valid addresses should not raise errors."""
        validate_address("123 Main Street")
        validate_address("Flat 5, 10-12 Oxford Street, London, UK")
        validate_address("PO Box 123, City, Country")

    def test_address_too_short(self):
        """Addresses shorter than minimum length should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_address("12")

    def test_address_too_long(self):
        """Addresses longer than maximum length should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_address("A" * 256)

    def test_empty_address(self):
        """Empty addresses should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_address("")

    def test_null_address(self):
        """None address should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_address(None)


class TestDateOfBirthValidation:
    """Tests for date of birth validation."""

    def test_valid_dates(self):
        """Valid dates of birth should not raise errors."""
        validate_date_of_birth(date(1990, 5, 15))
        validate_date_of_birth(date(1950, 1, 1))
        validate_date_of_birth(date(2000, 12, 31))

    def test_future_date(self):
        """Future dates should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_date_of_birth(date(2050, 1, 1))

    def test_too_old_date(self):
        """Dates before 1900 should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_date_of_birth(date(1899, 12, 31))

    def test_extremely_old_age(self):
        """Ages exceeding maximum should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_date_of_birth(date(1800, 1, 1))

    def test_null_date(self):
        """None date should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_date_of_birth(None)

    def test_invalid_date_type(self):
        """Non-date types should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_date_of_birth("1990-01-01")


class TestNationalityValidation:
    """Tests for nationality validation."""

    def test_valid_nationalities(self):
        """Valid nationality strings should not raise errors."""
        validate_nationality("British")
        validate_nationality("French")
        validate_nationality("United States")

    def test_empty_nationality(self):
        """Empty nationality should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_nationality("")

    def test_null_nationality(self):
        """None nationality should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_nationality(None)

    def test_nationality_too_long(self):
        """Nationalities exceeding maximum length should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_nationality("A" * 101)
