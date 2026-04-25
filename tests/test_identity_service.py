import pytest
from datetime import date
from src.platform import DigitalIDPlatform
from src.models.digital_id import IDStatus, OrganisationType
from src.auth.organisation_auth import OrganisationAuth
from src.exceptions import InvalidOperationError, PermissionError


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

    def test_immutable_identity_fields_cannot_be_reassigned(self, platform, central):
        digital_id = platform.identity.create_digital_id(
            central, "ID003", "Alice Jones",
            date(1991, 7, 8), "British", "1 High Street", "alice.jones@test.com"
        )

        with pytest.raises(AttributeError):
            digital_id.full_name = "Changed Name"

        with pytest.raises(AttributeError):
            digital_id.nationality = "French"


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

    def test_suspend_already_suspended_raises_error(self, platform, central, active_id):
        platform.identity.suspend_id(central, active_id.id_number)
        with pytest.raises(InvalidOperationError, match="ACTIVE"):
            platform.identity.suspend_id(central, active_id.id_number)

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


class TestQueryMethods:

    def test_find_ids_by_name_is_case_insensitive_substring(self, platform, central):
        platform.identity.create_digital_id(
            central, "ID100", "Alice Smith",
            date(1990, 1, 1), "British", "1 A St", "alice@test.com"
        )
        platform.identity.create_digital_id(
            central, "ID101", "ALICIA Turner",
            date(1991, 1, 1), "Irish", "2 B St", "alicia@test.com"
        )

        matches = platform.identity.find_ids_by_name("ali")
        assert sorted(d.id_number for d in matches) == ["ID100", "ID101"]

    def test_find_ids_by_status(self, platform, central):
        pending = platform.identity.create_digital_id(
            central, "ID110", "Pending Person",
            date(1990, 1, 1), "British", "1 P St", "pending@test.com"
        )
        active = platform.identity.create_digital_id(
            central, "ID111", "Active Person",
            date(1990, 2, 1), "British", "2 P St", "active@test.com"
        )
        platform.identity.activate_id(central, active.id_number)

        results = platform.identity.find_ids_by_status(IDStatus.PENDING)
        assert [d.id_number for d in results] == [pending.id_number]

    def test_find_ids_by_nationality(self, platform, central):
        platform.identity.create_digital_id(
            central, "ID120", "A One",
            date(1990, 1, 1), "British", "1 N St", "a1@test.com"
        )
        platform.identity.create_digital_id(
            central, "ID121", "A Two",
            date(1991, 1, 1), "French", "2 N St", "a2@test.com"
        )

        matches = platform.identity.find_ids_by_nationality("French")
        assert [d.id_number for d in matches] == ["ID121"]

    def test_count_ids(self, platform, central):
        assert platform.identity.count_ids() == 0
        platform.identity.create_digital_id(
            central, "ID130", "One Person",
            date(1990, 1, 1), "British", "1 C St", "one@test.com"
        )
        platform.identity.create_digital_id(
            central, "ID131", "Two Person",
            date(1990, 2, 1), "British", "2 C St", "two@test.com"
        )
        assert platform.identity.count_ids() == 2

    def test_get_all_ids_returns_all_created_ids(self, platform, central):
        created = [
            platform.identity.create_digital_id(
                central, "ID140", "X Person",
                date(1990, 1, 1), "British", "1 G St", "x@test.com"
            ),
            platform.identity.create_digital_id(
                central, "ID141", "Y Person",
                date(1990, 2, 1), "Irish", "2 G St", "y@test.com"
            ),
        ]

        all_ids = platform.identity.get_all_ids()
        assert sorted(d.id_number for d in all_ids) == sorted(d.id_number for d in created)


class TestSuspensionOverlapBoundaries:

    def test_ongoing_suspension_overlaps_query_period(self, active_id):
        active_id.suspension_history = [(date(2026, 5, 1), None)]
        assert active_id.was_suspended_during(date(2026, 5, 10), date(2026, 5, 20)) is True

    def test_ongoing_suspension_starting_after_query_period_does_not_overlap(self, active_id):
        active_id.suspension_history = [(date(2026, 6, 1), None)]
        assert active_id.was_suspended_during(date(2026, 5, 1), date(2026, 5, 31)) is False

    def test_closed_suspension_outside_range_does_not_overlap(self, active_id):
        active_id.suspension_history = [(date(2026, 1, 1), date(2026, 1, 10))]
        assert active_id.was_suspended_during(date(2026, 2, 1), date(2026, 2, 28)) is False

    def test_exact_boundary_touch_counts_as_overlap(self, active_id):
        active_id.suspension_history = [(date(2026, 4, 1), date(2026, 4, 10))]
        assert active_id.was_suspended_during(date(2026, 4, 10), date(2026, 4, 20)) is True

    def test_closed_suspension_before_query_period_does_not_overlap(self, active_id):
        active_id.suspension_history = [(date(2026, 3, 1), date(2026, 3, 15))]
        assert active_id.was_suspended_during(date(2026, 3, 16), date(2026, 3, 31)) is False

