import sys
from unittest.mock import MagicMock, patch

# Mock google.cloud modules BEFORE importing src.integrations.scc
mock_sc = MagicMock()
mock_pb = MagicMock()

# Setup module mocks in sys.modules so import succeeds
sys.modules["google.cloud"] = MagicMock()
# We set this so proper import happens, but we will patch the module attribute in tests
sys.modules["google.cloud.securitycenter"] = mock_sc
sys.modules["google.protobuf"] = MagicMock()
sys.modules["google.protobuf.timestamp_pb2"] = mock_pb

# Import the module under test
import importlib

from src.core.models import Finding
from src.integrations import scc

# Reload to ensure it picks up the sys.modules mocks if it was already imported
importlib.reload(scc)
from src.integrations.scc import SCCExporter


class TestSCCExporter:
    # Use patch on the imported module's attribute
    # This guarantees we are validating against what the code actually uses
    @patch("src.integrations.scc.securitycenter")
    def test_init_success(self, mock_securitycenter):
        # Setup the mock class inside the module
        mock_client = MagicMock()
        mock_securitycenter.SecurityCenterClient.return_value = mock_client

        exporter = SCCExporter("org-123", "source-456")

        assert exporter.org_id == "org-123"
        assert exporter.source_id == "source-456"
        assert exporter.parent == "organizations/org-123/sources/source-456"
        mock_securitycenter.SecurityCenterClient.assert_called_once()

    @patch("src.integrations.scc.securitycenter")
    def test_export_success(self, mock_securitycenter):
        # Setup mock client
        mock_client = MagicMock()
        mock_securitycenter.SecurityCenterClient.return_value = mock_client

        # Setup Enums on the patched object
        mock_securitycenter.Finding.State.ACTIVE = 1
        mock_securitycenter.Finding.Severity.CRITICAL = 1
        mock_securitycenter.Finding.Severity.SEVERITY_UNSPECIFIED = 0

        exporter = SCCExporter("org-1", "source-1")

        findings = [
            Finding(
                id="TEST_FINDING",
                severity="CRITICAL",
                description="Test description",
                resource="//cloudresourcemanager.googleapis.com/projects/p1",
                details={"key": "value"},
            )
        ]

        count = exporter.export(findings)

        assert count == 1
        mock_client.create_finding.assert_called_once()

        # Verify call args for create_finding (parent and finding_id)
        call_args = mock_client.create_finding.call_args[1]
        assert call_args["request"]["parent"] == "organizations/org-1/sources/source-1"
        assert "finding_id" in call_args["request"]

        # Verify that Finding() was called with correct parameters
        # We check the call to the Finding constructor
        mock_securitycenter.Finding.assert_called()
        finding_call_kwargs = mock_securitycenter.Finding.call_args[1]
        assert finding_call_kwargs["category"] == "TEST_FINDING"
        assert finding_call_kwargs["description"] == "Test description"
        assert finding_call_kwargs["severity"] == 1  # CRITICAL mock value

    @patch("src.integrations.scc.securitycenter")
    def test_export_failure_logs_error(self, mock_securitycenter):
        mock_client = MagicMock()
        mock_client.create_finding.side_effect = Exception("API Error")
        mock_securitycenter.SecurityCenterClient.return_value = mock_client

        # Setup Enums
        mock_securitycenter.Finding.Severity.LOW = 4
        mock_securitycenter.Finding.Severity.SEVERITY_UNSPECIFIED = 0
        mock_securitycenter.Finding.State.ACTIVE = 1

        exporter = SCCExporter("org-1", "source-1")
        findings = [Finding(id="FAIL", severity="LOW", description="Fail", resource="res")]

        count = exporter.export(findings)

        assert count == 0
        mock_client.create_finding.assert_called_once()
