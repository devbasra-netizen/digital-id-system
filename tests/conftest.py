"""Shared pytest fixtures for the test suite.

Pulled out of the individual test modules so the same organisations and
starter IDs are built the same way everywhere.
"""

import pytest
from datetime import date

from src.platform import DigitalIDPlatform
from src.models.digital_id import OrganisationType
from src.auth.organisation_auth import OrganisationAuth


@pytest.fixture
def platform():
    """A fresh platform per test, with empty store and empty audit log."""
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
def pending_id(platform, central):
    """A freshly created ID still in PENDING state."""
    return platform.identity.create_digital_id(
        central, "TEST001", "Jane Doe",
        date(1992, 6, 10), "British", "1 Test Lane", "jane@test.com"
    )


@pytest.fixture
def active_id(platform, central, pending_id):
    """The pending fixture, advanced to ACTIVE."""
    platform.identity.activate_id(central, pending_id.id_number)
    return pending_id
