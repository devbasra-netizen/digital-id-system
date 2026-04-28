"""Tests for the AuditLog module."""

import pytest
from src.audit.audit_log import AuditLog


@pytest.fixture
def audit():
    return AuditLog()


class TestAuditRecord:

    def test_record_adds_entry(self, audit):
        audit.record("Home Ministry", "CREATE_ID", "ID001", "Created.", True)
        assert audit.get_entries_count() == 1

    def test_entry_fields_stored_correctly(self, audit):
        audit.record("HMRC", "VERIFY_WITH_HISTORY", "ID002", "Checked.", True)
        entry = audit.get_all_entries()[0]
        assert entry.organisation == "HMRC"
        assert entry.operation == "VERIFY_WITH_HISTORY"
        assert entry.id_number == "ID002"
        assert entry.details == "Checked."
        assert entry.success is True

    def test_failed_entry_stored(self, audit):
        audit.record("Barclays", "VERIFY_BASIC", "ID003", "Denied.", False)
        entry = audit.get_all_entries()[0]
        assert entry.success is False

    def test_multiple_entries_preserve_order(self, audit):
        audit.record("A", "OP1", "ID1", "first", True)
        audit.record("B", "OP2", "ID2", "second", False)
        entries = audit.get_all_entries()
        assert len(entries) == 2
        assert entries[0].details == "first"
        assert entries[1].details == "second"

    def test_entries_are_immutable(self, audit):
        audit.record("A", "OP1", "ID1", "original", True)
        entry = audit.get_all_entries()[0]

        with pytest.raises(AttributeError):
            entry.details = "edited"


class TestAuditQueries:

    def test_get_entries_for_id(self, audit):
        audit.record("A", "OP", "ID001", "d1", True)
        audit.record("B", "OP", "ID002", "d2", True)
        audit.record("A", "OP", "ID001", "d3", False)
        assert len(audit.get_entries_for_id("ID001")) == 2

    def test_get_entries_by_operation(self, audit):
        audit.record("A", "CREATE_ID", "ID1", "d", True)
        audit.record("A", "ACTIVATE_ID", "ID1", "d", True)
        audit.record("B", "CREATE_ID", "ID2", "d", True)
        assert len(audit.get_entries_by_operation("CREATE_ID")) == 2

    def test_get_entries_by_organisation(self, audit):
        audit.record("HMRC", "OP", "ID1", "d", True)
        audit.record("DVLA", "OP", "ID1", "d", True)
        audit.record("HMRC", "OP", "ID2", "d", False)
        assert len(audit.get_entries_by_organisation("HMRC")) == 2

    def test_get_failed_entries(self, audit):
        audit.record("A", "OP", "ID1", "ok", True)
        audit.record("A", "OP", "ID2", "fail", False)
        audit.record("A", "OP", "ID3", "fail2", False)
        assert len(audit.get_failed_entries()) == 2

    def test_get_successful_entries(self, audit):
        audit.record("A", "OP", "ID1", "ok1", True)
        audit.record("A", "OP", "ID2", "fail", False)
        audit.record("A", "OP", "ID3", "ok2", True)
        assert len(audit.get_successful_entries()) == 2

    def test_empty_log_returns_empty_lists(self, audit):
        assert audit.get_all_entries() == []
        assert audit.get_failed_entries() == []
        assert audit.get_entries_for_id("X") == []
        assert audit.get_entries_count() == 0


class TestAuditDisplay:

    def test_display_empty_log_message(self, audit, capsys):
        audit.display()
        output = capsys.readouterr().out
        assert "No audit entries recorded." in output

    def test_display_prints_entries_with_status_marker(self, audit, capsys):
        audit.record("Home Ministry", "CREATE_ID", "ID001", "Created.", True)
        audit.record("HMRC", "VERIFY_WITH_HISTORY", "ID001", "Denied.", False)

        audit.display()
        output = capsys.readouterr().out

        assert "AUDIT LOG" in output
        assert "[OK" in output
        assert "[FAIL" in output
        assert "CREATE_ID" in output
        assert "VERIFY_WITH_HISTORY" in output
