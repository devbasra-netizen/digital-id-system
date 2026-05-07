"""Console demo for the Digital ID coursework.

Walks through each capability the platform supports so the marker can see
the system behaving end-to-end without having to read individual tests.
"""
from datetime import date

from src.platform import DigitalIDPlatform
from src.models.digital_id import OrganisationType, IDStatus
from src.auth.organisation_auth import OrganisationAuth
from src.exceptions import ValidationError, InvalidOperationError, PermissionError


def section(title: str) -> None:
    print(f"\n{'-' * 70}")
    print(f"  {title}")
    print(f"{'-' * 70}")


def line(message: str) -> None:
    print(f"  -> {message}")


def main() -> None:
    platform = DigitalIDPlatform()

    # Set up the organisations used in the walkthrough.
    home_ministry = OrganisationAuth(OrganisationType.CENTRAL_AUTHORITY, "Home Ministry")
    hmrc = OrganisationAuth(OrganisationType.TAX_AUTHORITY, "HMRC")
    dvla = OrganisationAuth(OrganisationType.DRIVING_LICENCE_AUTHORITY, "DVLA")
    barclays = OrganisationAuth(OrganisationType.BANK, "Barclays Bank")
    acme = OrganisationAuth(OrganisationType.EMPLOYER, "Acme Corp")
    welfare = OrganisationAuth(OrganisationType.WELFARE_SERVICE, "Dept of Work & Pensions")

    print("\n" + "=" * 70)
    print("   DIGITAL ID PLATFORM - DEMO RUN")
    print("=" * 70)
    print("   Walking through the core features and rule checks.")

    # 1. Create a few sample IDs (Central Authority only).
    section("1. Creating Digital IDs (Central Authority Only)")
    try:
        alice = platform.identity.create_digital_id(
            home_ministry, "ID001", "Alice Smith",
            date(1990, 5, 15), "British", "123 Main St, London", "alice@example.com"
        )
        line(f"Created: {alice}")

        bob = platform.identity.create_digital_id(
            home_ministry, "ID002", "Bob Jones",
            date(1985, 3, 22), "British", "456 Oak Ave, Manchester", "bob@example.com"
        )
        line(f"Created: {bob}")

        charlie = platform.identity.create_digital_id(
            home_ministry, "ID003", "Charlie Brown",
            date(1992, 12, 10), "British", "789 Pine Rd, Birmingham", "charlie@example.com"
        )
        line(f"Created: {charlie}")
    except (ValidationError, PermissionError) as e:
        line(f"Error: {e}")

    # 2. Show validation rejecting bad input.
    section("2. Input Validation")
    try:
        platform.identity.create_digital_id(
            home_ministry, "ID004", "David Invalid",
            date(1995, 1, 1), "British", "123 St", "not-an-email"
        )
    except ValidationError as e:
        line(f"Email validation caught (expected): {type(e).__name__}")

    try:
        platform.identity.create_digital_id(
            home_ministry, "ID005", "Eve Future",
            date(2030, 1, 1), "British", "123 St", "eve@test.com"
        )
    except ValidationError as e:
        line(f"Date validation caught (expected): {type(e).__name__}")

    # 3. Permission rejection: a bank tries to create an ID.
    section("3. Permission Enforcement")
    try:
        platform.identity.create_digital_id(
            barclays, "ID100", "Frank Faker",
            date(1980, 1, 1), "British", "123 St", "frank@test.com"
        )
    except PermissionError as e:
        line(f"Creation rejected (only Central Authority): {type(e).__name__}")

    # 4. Walk Alice through the full status lifecycle.
    section("4. Digital ID Status Lifecycle")
    line(f"Alice initial status: {alice.status.value}")

    platform.identity.activate_id(home_ministry, "ID001")
    line(f"After activate: {alice.status.value}")

    platform.identity.activate_id(home_ministry, "ID001")  # second call should be a no-op
    line(f"Activate again (idempotent): {alice.status.value}")

    platform.identity.suspend_id(home_ministry, "ID001")
    line(f"After suspend: {alice.status.value}")

    platform.identity.reinstate_id(home_ministry, "ID001")
    line(f"After reinstate: {alice.status.value}")

    # Activate the others so the verification examples below have something to work on.
    platform.identity.activate_id(home_ministry, "ID002")
    platform.identity.activate_id(home_ministry, "ID003")

    # 5. Basic verification (banks, employers, welfare).
    section("5. Basic Verification (Banks, Employers)")
    result = platform.verification.verify_basic(barclays, "ID001")
    line(f"Barclays verifies Alice: {result.is_valid} ({result.message})")

    result = platform.verification.verify_basic(acme, "ID001")
    line(f"Acme Corp verifies Alice: {result.is_valid} ({result.message})")

    result = platform.verification.verify_basic(welfare, "ID003")
    line(f"DWP verifies Charlie: {result.is_valid} ({result.message})")

    # 6. Mutable attribute updates (only Central Authority).
    section("6. Updating Mutable Attributes")
    line(f"Alice's original address: {alice.address}")

    platform.identity.update_address(home_ministry, "ID001", "999 New Road, London")
    line(f"Alice's new address: {alice.address}")

    platform.identity.update_email(home_ministry, "ID001", "alice.smith@newdomain.co.uk")
    line(f"Alice's new email: {alice.email}")

    # 7. Restriction flag and DVLA's eligibility check.
    section("7. Restriction Flags (DVLA Check)")
    result = platform.verification.verify_with_restriction_check(dvla, "ID001")
    line(f"DVLA: Alice (no restriction): {result.is_valid}")

    platform.identity.set_restriction(home_ministry, "ID001", True)
    result = platform.verification.verify_with_restriction_check(dvla, "ID001")
    line(f"DVLA: Alice (with restriction): {result.is_valid} - {result.message}")

    platform.identity.set_restriction(home_ministry, "ID001", False)

    # 8. Suspension history overlap (HMRC reporting period check).
    section("8. Suspension History (Tax Compliance Checks)")
    line(f"Bob's suspension history before: {len(bob.suspension_history)} records")

    platform.identity.suspend_id(home_ministry, "ID002")
    line(f"Bob suspended on {bob.suspension_history[-1][0]}")

    result = platform.verification.verify_with_history(
        hmrc, "ID002", date(2026, 1, 1), date(2026, 12, 31)
    )
    line(f"HMRC: Bob suspended during 2026: {result.is_valid}")

    platform.identity.reinstate_id(home_ministry, "ID002")
    line(f"Bob reinstated on {bob.suspension_history[-1][1]} (suspension closed)")

    result = platform.verification.verify_with_history(
        hmrc, "ID002", date(2026, 1, 1), date(2026, 12, 31)
    )
    line(f"HMRC: Bob after reinstate: {result.is_valid}")

    # 9. Revoke is terminal.
    section("9. Revoke (Terminal State)")
    line(f"Charlie status before revoke: {charlie.status.value}")

    platform.identity.revoke_id(home_ministry, "ID003")
    line(f"Charlie status after revoke: {charlie.status.value}")
    line("Revoked IDs cannot be modified or transitioned.")

    try:
        platform.identity.update_address(home_ministry, "ID003", "New Address")
    except InvalidOperationError as e:
        line(f"  Update rejected: {type(e).__name__}")

    try:
        platform.identity.activate_id(home_ministry, "ID003")
    except InvalidOperationError as e:
        line(f"  Activate rejected: {type(e).__name__}")

    # 10. Search / query helpers.
    section("10. Search and query examples")
    line(f"Total Digital IDs in system: {platform.identity.count_ids()}")

    active_ids = platform.identity.find_ids_by_status(IDStatus.ACTIVE)
    line(f"IDs with ACTIVE status: {len(active_ids)}")

    british_ids = platform.identity.find_ids_by_nationality("British")
    line(f"IDs with British nationality: {len(british_ids)}")

    smith_ids = platform.identity.find_ids_by_name("Smith")
    line(f"IDs matching name pattern 'Smith': {[d.full_name for d in smith_ids]}")

    # 11. Verification permissions (each role only sees what it should).
    section("11. Verification permissions")
    try:
        platform.verification.verify_basic(hmrc, "ID001")
    except PermissionError:
        line("HMRC cannot use basic verify: Permission denied")

    try:
        platform.verification.verify_with_history(
            barclays, "ID001", date(2026, 1, 1), date(2026, 12, 31)
        )
    except PermissionError:
        line("Barclays cannot use history verify: Permission denied")

    # 12. Audit trail summary.
    section("12. Full Audit Trail")
    total_entries = len(platform.audit.get_all_entries())
    line(f"Total audit entries recorded: {total_entries}")

    alice_entries = platform.audit.get_entries_for_id("ID001")
    line(f"Operations on Alice (ID001): {len(alice_entries)} entries")

    failed_entries = platform.audit.get_failed_entries()
    line(f"Failed operations (validation/permission): {len(failed_entries)} entries")

    hmrc_count = len(platform.audit.get_entries_by_organisation("HMRC"))
    line(f"All operations for HMRC: {hmrc_count} entries")

    print("\n" + "=" * 70)
    print("   AUDIT LOG - ALL RECORDED ACTIVITY")
    print("=" * 70)
    platform.audit.display()

    print("\n" + "=" * 70)
    print("   DEMO COMPLETE")
    print("=" * 70)
    print("   - Core functionality shown")
    print("   - Permission checks shown")
    print("   - Status transitions shown")
    print("   - Audit trail shown")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
