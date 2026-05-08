"""Tests for VerificationService: the three verification modes."""

import pytest
from datetime import date

from src.platform import DigitalIDPlatform
from src.models.digital_id import OrganisationType
from src.auth.organisation_auth import OrganisationAuth
from src.exceptions import PermissionError, ValidationError


# Fixtures

@pytest.fixture
def platform():
    return DigitalIDPlatform()


@pytest.fixture
def central():
    return OrganisationAuth(OrganisationType.CENTRAL_AUTHORITY, "Home Ministry")


@pytest.fixture
def bank():
    return OrganisationAuth(OrganisationType.BANK, "Test Bank")


@pytest.fixture
def tax():
    return OrganisationAuth(OrganisationType.TAX_AUTHORITY, "HMRC")


@pytest.fixture
def dvla():
    return OrganisationAuth(OrganisationType.DRIVING_LICENCE_AUTHORITY, "DVLA")


@pytest.fixture
def employer():
    return OrganisationAuth(OrganisationType.EMPLOYER, "Acme Corp")


@pytest.fixture
def active_id(platform, central):
    digital_id = platform.identity.create_digital_id(
        central, "TEST001", "Jane Doe",
        date(1992, 6, 10), "British", "1 Test Lane", "jane@test.com"
    )
    platform.identity.activate_id(central, "TEST001")
    return digital_id


# Basic verification (banks, employers, welfare, local authority)

class TestBasicVerification:

    def test_active_id_is_valid(self, platform, bank, active_id):
        result = platform.verification.verify_basic(bank, active_id.id_number)
        assert result.is_valid is True

    def test_pending_id_is_invalid(self, platform, bank, central):
        platform.identity.create_digital_id(
            central, "PEND01", "Pending Person",
            date(2000, 1, 1), "British", "1 Pending St", "p@test.com"
        )
        result = platform.verification.verify_basic(bank, "PEND01")
        assert result.is_valid is False

    def test_suspended_id_is_invalid(self, platform, bank, central, active_id):
        platform.identity.suspend_id(central, active_id.id_number)
        result = platform.verification.verify_basic(bank, active_id.id_number)
        assert result.is_valid is False

    def test_revoked_id_is_invalid(self, platform, bank, central, active_id):
        platform.identity.revoke_id(central, active_id.id_number)
        result = platform.verification.verify_basic(bank, active_id.id_number)
        assert result.is_valid is False

    def test_nonexistent_id_is_invalid(self, platform, bank):
        result = platform.verification.verify_basic(bank, "DOESNOTEXIST")
        assert result.is_valid is False

    def test_employer_can_verify_basic(self, platform, employer, active_id):
        result = platform.verification.verify_basic(employer, active_id.id_number)
        assert result.is_valid is True

    def test_tax_authority_cannot_use_basic_verify(self, platform, tax, active_id):
        with pytest.raises(PermissionError):
            platform.verification.verify_basic(tax, active_id.id_number)

    def test_dvla_cannot_use_basic_verify(self, platform, dvla, active_id):
        with pytest.raises(PermissionError):
            platform.verification.verify_basic(dvla, active_id.id_number)

    def test_result_repr_contains_validity_label(self, platform, bank, active_id):
        result = platform.verification.verify_basic(bank, active_id.id_number)
        assert "VALID" in repr(result)


# History verification (HMRC reporting period)

class TestHistoryVerification:

    def test_active_never_suspended_passes(self, platform, tax, active_id):
        result = platform.verification.verify_with_history(
            tax, active_id.id_number, date(2026, 1, 1), date(2026, 12, 31)
        )
        assert result.is_valid is True

    def test_currently_suspended_fails(self, platform, tax, central, active_id):
        platform.identity.suspend_id(central, active_id.id_number)
        result = platform.verification.verify_with_history(
            tax, active_id.id_number, date(2026, 1, 1), date(2026, 12, 31)
        )
        assert result.is_valid is False

    def test_was_suspended_in_period_fails(self, platform, tax, central, active_id):
        platform.identity.suspend_id(central, active_id.id_number)
        platform.identity.reinstate_id(central, active_id.id_number)
        result = platform.verification.verify_with_history(
            tax, active_id.id_number, date(2026, 1, 1), date(2026, 12, 31)
        )
        assert result.is_valid is False

    def test_revoked_id_fails_history_check(self, platform, tax, central, active_id):
        platform.identity.revoke_id(central, active_id.id_number)
        result = platform.verification.verify_with_history(
            tax, active_id.id_number, date(2026, 1, 1), date(2026, 12, 31)
        )
        assert result.is_valid is False

    def test_bank_cannot_use_history_verify(self, platform, bank, active_id):
        with pytest.raises(PermissionError):
            platform.verification.verify_with_history(
                bank, active_id.id_number, date(2026, 1, 1), date(2026, 12, 31)
            )

    def test_history_verify_rejects_start_after_end(self, platform, tax, active_id):
        with pytest.raises(ValidationError, match="start date"):
            platform.verification.verify_with_history(
                tax, active_id.id_number, date(2026, 12, 31), date(2026, 1, 1)
            )

        failed = platform.audit.get_failed_entries()
        assert failed[-1].operation == "VERIFY_WITH_HISTORY"
        assert failed[-1].id_number == active_id.id_number

    def test_history_verify_rejects_non_date_inputs(self, platform, tax, active_id):
        with pytest.raises(ValidationError, match="date objects"):
            platform.verification.verify_with_history(
                tax, active_id.id_number, "2026-01-01", "2026-12-31"
            )

    def test_history_nonexistent_id_is_invalid_and_audited(self, platform, tax):
        result = platform.verification.verify_with_history(
            tax, "MISSING-HISTORY", date(2026, 1, 1), date(2026, 12, 31)
        )
        assert result.is_valid is False

        failed = platform.audit.get_failed_entries()
        assert failed[-1].operation == "VERIFY_WITH_HISTORY"
        assert failed[-1].id_number == "MISSING-HISTORY"


# Restriction verification (DVLA eligibility check)

class TestRestrictionVerification:

    def test_active_no_restriction_passes(self, platform, dvla, active_id):
        result = platform.verification.verify_with_restriction_check(dvla, active_id.id_number)
        assert result.is_valid is True

    def test_active_with_restriction_fails(self, platform, dvla, central, active_id):
        platform.identity.set_restriction(central, active_id.id_number, True)
        result = platform.verification.verify_with_restriction_check(dvla, active_id.id_number)
        assert result.is_valid is False

    def test_suspended_with_no_restriction_fails(self, platform, dvla, central, active_id):
        platform.identity.suspend_id(central, active_id.id_number)
        result = platform.verification.verify_with_restriction_check(dvla, active_id.id_number)
        assert result.is_valid is False

    def test_clearing_restriction_allows_pass(self, platform, dvla, central, active_id):
        platform.identity.set_restriction(central, active_id.id_number, True)
        platform.identity.set_restriction(central, active_id.id_number, False)
        result = platform.verification.verify_with_restriction_check(dvla, active_id.id_number)
        assert result.is_valid is True

    def test_bank_cannot_use_restriction_verify(self, platform, bank, active_id):
        with pytest.raises(PermissionError):
            platform.verification.verify_with_restriction_check(bank, active_id.id_number)

    def test_tax_cannot_use_restriction_verify(self, platform, tax, active_id):
        with pytest.raises(PermissionError):
            platform.verification.verify_with_restriction_check(tax, active_id.id_number)

    def test_restriction_nonexistent_id_is_invalid_and_audited(self, platform, dvla):
        result = platform.verification.verify_with_restriction_check(dvla, "MISSING-RESTRICT")
        assert result.is_valid is False

        failed = platform.audit.get_failed_entries()
        assert failed[-1].operation == "VERIFY_WITH_RESTRICTION"
        assert failed[-1].id_number == "MISSING-RESTRICT"
