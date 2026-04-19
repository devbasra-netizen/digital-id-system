import pytest
from datetime import date
from src.platform import DigitalIDPlatform
from src.models.digital_id import IDStatus, OrganisationType
from src.auth.organisation_auth import OrganisationAuth


# ── Fixtures ─────────────────────────────────────────────────────────────────

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
def pending_id(platform, central):
    return platform.identity.create_digital_id(
        central, "TEST001", "John Doe",
        date(1990, 1, 1), "British", "1 Test Street", "john@test.com"
    )


@pytest.fixture
def active_id(platform, central, pending_id):
    platform.identity.activate_id(central, pending_id.id_number)
    return pending_id


# ── Create ────────────────────────────────────────────────────────────────────

class TestCreateDigitalID:

    def test_creates_with_pending_status(self, platform, central):
        digital_id = platform.identity.create_digital_id(
            central, "ID001", "Alice Smith",
            date(1990, 5, 15), "British", "123 Main St", "alice@test.com"
        )
        assert digital_id.id_number == "ID001"
        assert digital_id.full_name == "Alice Smith"
        assert digital_id.status == IDStatus.PENDING

    def test_immutable_fields_set_correctly(self, platform, central):
        digital_id = platform.identity.create_digital_id(
            central, "ID002", "Bob Jones",
            date(1985, 3, 22), "Irish", "456 Oak Ave", "bob@test.com"
        )
        assert digital_id.nationality == "Irish"
        assert digital_id.date_of_birth == date(1985, 3, 22)

    def test_duplicate_id_raises_error(self, platform, central, pending_id):
        with pytest.raises(ValueError, match="already exists"):
            platform.identity.create_digital_id(
                central, "TEST001", "Duplicate", date(2000, 1, 1),
                "British", "2 St", "dup@test.com"
            )

    def test_bank_cannot_create_id(self, platform, bank):
        with pytest.raises(PermissionError):
            platform.identity.create_digital_id(
                bank, "ID003", "Hacker", date(2000, 1, 1),
                "British", "3 St", "hack@test.com"
            )


# ── Status Transitions ────────────────────────────────────────────────────────

class TestStatusTransitions:

    def test_activate_pending_id(self, platform, central, pending_id):
        platform.identity.activate_id(central, pending_id.id_number)
        assert pending_id.status == IDStatus.ACTIVE

    def test_activate_is_idempotent(self, platform, central, active_id):
        platform.identity.activate_id(central, active_id.id_number)
        assert active_id.status == IDStatus.ACTIVE

    def test_suspend_active_id(self, platform, central, active_id):
        platform.identity.suspend_id(central, active_id.id_number)
        assert active_id.status == IDStatus.SUSPENDED

    def test_suspend_is_idempotent(self, platform, central, active_id):
        platform.identity.suspend_id(central, active_id.id_number)
        platform.identity.suspend_id(central, active_id.id_number)
        assert active_id.status == IDStatus.SUSPENDED

    def test_reinstate_suspended_id(self, platform, central, active_id):
        platform.identity.suspend_id(central, active_id.id_number)
        platform.identity.reinstate_id(central, active_id.id_number)
        assert active_id.status == IDStatus.ACTIVE

    def test_revoke_is_terminal(self, platform, central, active_id):
        platform.identity.revoke_id(central, active_id.id_number)
        assert active_id.status == IDStatus.REVOKED

    def test_revoke_is_idempotent(self, platform, central, active_id):
        platform.identity.revoke_id(central, active_id.id_number)
        platform.identity.revoke_id(central, active_id.id_number)
        assert active_id.status == IDStatus.REVOKED

    def test_cannot_activate_revoked_id(self, platform, central, active_id):
        platform.identity.revoke_id(central, active_id.id_number)
        with pytest.raises(ValueError, match="revoked"):
            platform.identity.activate_id(central, active_id.id_number)

    def test_cannot_suspend_revoked_id(self, platform, central, active_id):
        platform.identity.revoke_id(central, active_id.id_number)
        with pytest.raises(ValueError, match="revoked"):
            platform.identity.suspend_id(central, active_id.id_number)

    def test_cannot_reinstate_active_id(self, platform, central, active_id):
        with pytest.raises(ValueError):
            platform.identity.reinstate_id(central, active_id.id_number)

    def test_suspension_history_recorded(self, platform, central, active_id):
        platform.identity.suspend_id(central, active_id.id_number)
        assert len(active_id.suspension_history) == 1

    def test_suspension_closed_on_reinstate(self, platform, central, active_id):
        platform.identity.suspend_id(central, active_id.id_number)
        platform.identity.reinstate_id(central, active_id.id_number)
        start, end = active_id.suspension_history[0]
        assert end is not None


# ── Updates ───────────────────────────────────────────────────────────────────

class TestUpdateOperations:

    def test_update_address(self, platform, central, active_id):
        platform.identity.update_address(central, active_id.id_number, "New Address")
        assert active_id.address == "New Address"

    def test_update_email(self, platform, central, active_id):
        platform.identity.update_email(central, active_id.id_number, "new@test.com")
        assert active_id.email == "new@test.com"

    def test_set_restriction_flag(self, platform, central, active_id):
        platform.identity.set_restriction(central, active_id.id_number, True)
        assert active_id.has_restriction is True

    def test_clear_restriction_flag(self, platform, central, active_id):
        platform.identity.set_restriction(central, active_id.id_number, True)
        platform.identity.set_restriction(central, active_id.id_number, False)
        assert active_id.has_restriction is False

    def test_cannot_update_address_on_revoked_id(self, platform, central, active_id):
        platform.identity.revoke_id(central, active_id.id_number)
        with pytest.raises(ValueError, match="revoked"):
            platform.identity.update_address(central, active_id.id_number, "Hack")

    def test_cannot_update_email_on_revoked_id(self, platform, central, active_id):
        platform.identity.revoke_id(central, active_id.id_number)
        with pytest.raises(ValueError, match="revoked"):
            platform.identity.update_email(central, active_id.id_number, "hack@test.com")

    def test_bank_cannot_update_address(self, platform, bank, active_id):
        with pytest.raises(PermissionError):
            platform.identity.update_address(bank, active_id.id_number, "Hack Address")
