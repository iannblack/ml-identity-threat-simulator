"""Tests for remediation module."""

import pytest
from src.core.models import Finding
from src.iam.remediation import GcpRemediator, RemediationFactory


@pytest.fixture
def wildcard_finding():
    return Finding(
        id="WILDCARD_ACCESS",
        severity="CRITICAL",
        description="Public access detected",
        details={"role": "roles/viewer", "member": "allUsers"},
        remediation="Remove public access",
    )


class TestGcpRemediator:
    def test_wildcard_remediation(self, wildcard_finding):
        remediator = GcpRemediator(project_id="test-project")
        cmd = remediator.generate_remediation_command(wildcard_finding)

        assert cmd is not None
        assert "gcloud projects remove-iam-policy-binding test-project" in cmd
        assert "--member='allUsers'" in cmd
        assert "--role='roles/viewer'" in cmd

    def test_script_generation(self, wildcard_finding):
        remediator = GcpRemediator(project_id="test-project")
        script = remediator.generate_script([wildcard_finding])

        assert "#!/bin/bash" in script
        assert "gcloud projects" in script
        assert "# Auto-generated" in script


class TestRemediationFactory:
    def test_get_remediator(self):
        assert isinstance(RemediationFactory.get_remediator("gcp"), GcpRemediator)

        with pytest.raises(ValueError, match=r"Unknown provider: invalid"):
            RemediationFactory.get_remediator("invalid")
