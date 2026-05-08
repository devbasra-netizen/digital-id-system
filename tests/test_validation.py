"""Tests for the input validators."""

import pytest
from datetime import date

from src.validators import (
    validate_id_number, validate_name, validate_email, validate_address,
    validate_date_of_birth, validate_nationality
)
from src.exceptions import ValidationError


class TestIDNumberValidation:

    def test_valid_id_number(self):
        validate_id_number("ID001")
        validate_id_number("ABC-123-XYZ")
        validate_id_number("12345")

    def test_empty_id_number(self):
        with pytest.raises(ValidationError):
            validate_id_number("")

    def test_null_id_number(self):
        with pytest.raises(ValidationError):
            validate_id_number(None)

    def test_whitespace_only_id(self):
        with pytest.raises(ValidationError):
            validate_id_number("   ")

    def test_max_length_id_number_is_allowed(self):
        validate_id_number("A" * 50)

    def test_too_long_id_number_raises(self):
        with pytest.raises(ValidationError):
            validate_id_number("A" * 51)


class TestNameValidation:

    def test_valid_name(self):
        validate_name("John Smith")
        validate_name("Mary O'Brien")
        validate_name("José García")

    def test_name_too_short(self):
        with pytest.raises(ValidationError):
            validate_name("A")

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            validate_name("A" * 101)

    def test_empty_name(self):
        with pytest.raises(ValidationError):
            validate_name("")

    def test_null_name(self):
        with pytest.raises(ValidationError):
            validate_name(None)

    def test_whitespace_name_rejected(self):
        with pytest.raises(ValidationError):
            validate_name("   ")


class TestEmailValidation:

    def test_valid_emails(self):
        validate_email("user@example.com")
        validate_email("john.smith@company.co.uk")
        validate_email("mary+tag@domain.org")

    def test_invalid_email_formats(self):
        with pytest.raises(ValidationError):
            validate_email("notanemail")

        with pytest.raises(ValidationError):
            validate_email("@example.com")

        with pytest.raises(ValidationError):
            validate_email("user@")

        with pytest.raises(ValidationError):
            validate_email("user @example.com")

    def test_empty_email(self):
        with pytest.raises(ValidationError):
            validate_email("")

    def test_null_email(self):
        with pytest.raises(ValidationError):
            validate_email(None)

    def test_whitespace_email_rejected(self):
        with pytest.raises(ValidationError):
            validate_email("   ")


class TestAddressValidation:

    def test_valid_addresses(self):
        validate_address("123 Main Street")
        validate_address("Flat 5, 10-12 Oxford Street, London, UK")
        validate_address("PO Box 123, City, Country")

    def test_address_too_short(self):
        with pytest.raises(ValidationError):
            validate_address("12")

    def test_address_too_long(self):
        with pytest.raises(ValidationError):
            validate_address("A" * 256)

    def test_empty_address(self):
        with pytest.raises(ValidationError):
            validate_address("")

    def test_null_address(self):
        with pytest.raises(ValidationError):
            validate_address(None)

    def test_whitespace_address_rejected(self):
        with pytest.raises(ValidationError):
            validate_address("   ")


class TestDateOfBirthValidation:

    def test_valid_dates(self):
        validate_date_of_birth(date(1990, 5, 15))
        validate_date_of_birth(date(1950, 1, 1))
        validate_date_of_birth(date(2000, 12, 31))

    def test_future_date(self):
        with pytest.raises(ValidationError):
            validate_date_of_birth(date(2050, 1, 1))

    def test_too_old_date(self):
        with pytest.raises(ValidationError):
            validate_date_of_birth(date(1899, 12, 31))

    def test_extremely_old_age(self):
        with pytest.raises(ValidationError):
            validate_date_of_birth(date(1800, 1, 1))

    def test_null_date(self):
        with pytest.raises(ValidationError):
            validate_date_of_birth(None)

    def test_invalid_date_type(self):
        with pytest.raises(ValidationError):
            validate_date_of_birth("1990-01-01")

    def test_age_just_over_maximum_rejected(self):
        today = date.today()
        too_old = date(today.year - 151, today.month, today.day)
        with pytest.raises(ValidationError):
            validate_date_of_birth(too_old)


class TestNationalityValidation:

    def test_valid_nationalities(self):
        validate_nationality("British")
        validate_nationality("French")
        validate_nationality("United States")

    def test_empty_nationality(self):
        with pytest.raises(ValidationError):
            validate_nationality("")

    def test_null_nationality(self):
        with pytest.raises(ValidationError):
            validate_nationality(None)

    def test_nationality_too_long(self):
        with pytest.raises(ValidationError):
            validate_nationality("A" * 101)

    def test_whitespace_nationality_rejected(self):
        with pytest.raises(ValidationError):
            validate_nationality("   ")
