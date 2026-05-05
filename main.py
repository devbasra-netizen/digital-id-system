"""Small demo script I used to show the coursework features."""
from datetime import date
from src.platform import DigitalIDPlatform
from src.models.digital_id import OrganisationType, IDStatus
from src.auth.organisation_auth import OrganisationAuth
from src.exceptions import ValidationError, InvalidOperationError, PermissionError


def section(title: str) -> None:
    """Print a basic section header for demo output."""
    print(f"\n{'-' * 70}")
    print(f"  {title}")
    print(f"{'-' * 70}")


def demo_line(message: str) -> None:
    """Print one demo line with a small marker."""
    print(f"  -> {message}")


def main():
    platform = DigitalIDPlatform()

    # Organisations used in the examples below.
    home_ministry = OrganisationAuth(OrganisationType.CENTRAL_AUTHORITY, "Home Ministry")
    hmrc = OrganisationAuth(OrganisationType.TAX_AUTHORITY, "HMRC")
    dvla = OrganisationAuth(OrganisationType.DRIVING_LICENCE_AUTHORITY, "DVLA")
    barclays = OrganisationAuth(OrganisationType.BANK, "Barclays Bank")
    acme = OrganisationAuth(OrganisationType.EMPLOYER, "Acme Corp")
    welfare = OrganisationAuth(OrganisationType.WELFARE_SERVICE, "Dept of Work & Pensions")

    print("\n" + "=" * 70)
    print("   DIGITAL ID PLATFORM - DEMO RUN")
    print("=" * 70)
    print("   Running key features and rule checks")

    # 1) Create sample IDs
    section("1. Creating Digital IDs (Central Authority Only)")
    try:
        alice = platform.identity.create_digital_id(
            home_ministry, "ID001", "Alice Smith",
            date(1990, 5, 15), "British", "123 Main St, London", "alice@example.com"
        )
        demo_line(f"Created: {alice}")

        bob = platform.identity.create_digital_id(
            home_ministry, "ID002", "Bob Jones",
            date(1985, 3, 22), "British", "456 Oak Ave, Manchester", "bob@example.com"
        )
        demo_line(f"Created: {bob}")

        charlie = platform.identity.create_digital_id(
            home_ministry, "ID003", "Charlie Brown",
            date(1992, 12, 10), "British", "789 Pine Rd, Birmingham", "charlie@example.com"
        )
        demo_line(f"Created: {charlie}")
    except (ValidationError, PermissionError) as e:
        demo_line(f"Error: {e}")

    # 2) Show validation failures
    section("2. Input Validation")
    try:
        # Invalid email example
        platform.identity.create_digital_id(
            home_ministry, "ID004", "David Invalid",
            date(1995, 1, 1), "British", "123 St", "not-an-email"
        )
    except ValidationError as e:
        demo_line(f"Email validation caught (expected): {type(e).__name__}")

    try:
        # Future date of birth example
        platform.identity.create_digital_id(
            home_ministry, "ID005", "Eve Future",
            date(2030, 1, 1), "British", "123 St", "eve@test.com"
        )
    except ValidationError as e:
        demo_line(f"Date validation caught (expected): {type(e).__name__}")

    # 3) Permission checks
    section("3. Permission Enforcement")
    try:
        # Bank role is not allowed to create IDs
        platform.identity.create_digital_id(
            barclays, "ID100", "Frank Faker",
            date(1980, 1, 1), "British", "123 St", "frank@test.com"
        )
    except PermissionError as e:
        demo_line(f"Creation rejected (only Central Authority): {type(e).__name__}")

    # 4) Status changes
    section("4. Digital ID Status Lifecycle")
    demo_line(f"Alice initial status: {alice.status.value}")

    platform.identity.activate_id(home_ministry, "ID001")
    demo_line(f"After activate: {alice.status.value}")

    platform.identity.activate_id(home_ministry, "ID001")  # no-op on repeat call
    demo_line(f"Activate again (idempotent): {alice.status.value}")

    platform.identity.suspend_id(home_ministry, "ID001")
    demo_line(f"After suspend: {alice.status.value}")

    platform.identity.reinstate_id(home_ministry, "ID001")
    demo_line(f"After reinstate: {alice.status.value}")

    # Activate others for verification examples
    platform.identity.activate_id(home_ministry, "ID002")
    platform.identity.activate_id(home_ministry, "ID003")

    # 5) Basic verification
    section("5. Basic Verification (Banks, Employers)")
    result = platform.verification.verify_basic(barclays, "ID001")
    demo_line(f"Barclays verifies Alice: {result.is_valid} ({result.message})")

    result = platform.verification.verify_basic(acme, "ID001")
    demo_line(f"Acme Corp verifies Alice: {result.is_valid} ({result.message})")

    result = platform.verification.verify_basic(welfare, "ID003")
    demo_line(f"DWP verifies Charlie: {result.is_valid} ({result.message})")

    # 6) Update mutable fields
    section("6. Updating Mutable Attributes")
    demo_line(f"Alice's original address: {alice.address}")

    platform.identity.update_address(home_ministry, "ID001", "999 New Road, London")
    demo_line(f"Alice's new address: {alice.address}")

    platform.identity.update_email(home_ministry, "ID001", "alice.smith@newdomain.co.uk")
    demo_line(f"Alice's new email: {alice.email}")

    # 7) Restriction flag and DVLA checks
    section("7. Restriction Flags (DVLA Check)")
    result = platform.verification.verify_with_restriction_check(dvla, "ID001")
    demo_line(f"DVLA: Alice (no restriction): {result.is_valid}")

    platform.identity.set_restriction(home_ministry, "ID001", True)
    result = platform.verification.verify_with_restriction_check(dvla, "ID001")
    demo_line(f"DVLA: Alice (with restriction): {result.is_valid} - {result.message}")

    platform.identity.set_restriction(home_ministry, "ID001", False)

    # 8) Suspension history and HMRC checks
    section("8. Suspension History (Tax Compliance Checks)")
    demo_line(f"Bob's suspension history before: {len(bob.suspension_history)} records")

    platform.identity.suspend_id(home_ministry, "ID002")
    demo_line(f"Bob suspended on {bob.suspension_history[-1][0]}")

    result = platform.verification.verify_with_history(
        hmrc, "ID002", date(2026, 1, 1), date(2026, 12, 31)
    )
    demo_line(f"HMRC: Bob suspended during 2026: {result.is_valid}")

    platform.identity.reinstate_id(home_ministry, "ID002")
    demo_line(f"Bob reinstated on {bob.suspension_history[-1][1]} (suspension closed)")

    result = platform.verification.verify_with_history(
        hmrc, "ID002", date(2026, 1, 1), date(2026, 12, 31)
    )
    demo_line(f"HMRC: Bob after reinstate: {result.is_valid}")

    # 9) Revoke terminal state
    section("9. Revoke (Terminal State)")
    demo_line(f"Charlie status before revoke: {charlie.status.value}")

    platform.identity.revoke_id(home_ministry, "ID003")
    demo_line(f"Charlie status after revoke: {charlie.status.value}")
    demo_line("Revoked IDs cannot be modified or transitioned")

    try:
        platform.identity.update_address(home_ministry, "ID003", "New Address")
    except InvalidOperationError as e:
        demo_line(f"  Update rejected: {type(e).__name__}")

    try:
        platform.identity.activate_id(home_ministry, "ID003")
    except InvalidOperationError as e:
        demo_line(f"  Activate rejected: {type(e).__name__}")

    # 10) Query helper methods
    section("10. Search and query examples")
    demo_line(f"Total Digital IDs in system: {platform.identity.count_ids()}")

    active_ids = platform.identity.find_ids_by_status(IDStatus.ACTIVE)
    demo_line(f"IDs with ACTIVE status: {len(active_ids)}")

    british_ids = platform.identity.find_ids_by_nationality("British")
    demo_line(f"IDs with British nationality: {len(british_ids)}")

    smith_ids = platform.identity.find_ids_by_name("Smith")
    demo_line(f"IDs matching name pattern 'Smith': {[id.full_name for id in smith_ids]}")

    # 11) More permission examples
    section("11. Verification permissions")
    try:
        # HMRC role cannot use basic verification
        platform.verification.verify_basic(hmrc, "ID001")
    except PermissionError:
        demo_line("HMRC cannot use basic verify: Permission denied")

    try:
        # Bank role cannot use history verification
        platform.verification.verify_with_history(
            barclays, "ID001", date(2026, 1, 1), date(2026, 12, 31)
        )
    except PermissionError:
        demo_line("Barclays cannot use history verify: Permission denied")

    # 12) Print full audit trail
    section("12. Full Audit Trail")
    total_entries = len(platform.audit.get_all_entries())
    demo_line(f"Total audit entries recorded: {total_entries}")

    alice_entries = platform.audit.get_entries_for_id("ID001")
    demo_line(f"Operations on Alice (ID001): {len(alice_entries)} entries")

    failed_entries = platform.audit.get_failed_entries()
    demo_line(f"Failed operations (validation/permission): {len(failed_entries)} entries")

    hmrc_count = len(platform.audit.get_entries_by_organisation("HMRC"))
    demo_line(f"All operations for HMRC: {hmrc_count} entries")

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
