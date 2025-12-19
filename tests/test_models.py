"""
Comprehensive tests for core.models module.
Tests all Pydantic models for validation, serialization, and edge cases.
"""

import pytest
from pydantic import ValidationError

from src.core.models import Binding, Finding, Policy, ScenarioCheck, ScenarioResult


class TestBinding:
    """Tests for the Binding model."""

    def test_binding_creation_valid(self):
        """Test creating a valid binding."""
        binding = Binding(role="roles/viewer", members=["user:test@example.com"])
        assert binding.role == "roles/viewer"
        assert binding.members == ["user:test@example.com"]
        assert binding.condition is None

    def test_binding_with_condition(self):
        """Test binding with IAM condition."""
        condition = {"expression": "resource.name.startsWith('projects/_/buckets/bucket-name')"}
        binding = Binding(
            role="roles/storage.admin", members=["user:admin@example.com"], condition=condition
        )
        assert binding.condition == condition

    def test_binding_empty_members(self):
        """Test binding with empty members list."""
        binding = Binding(role="roles/viewer", members=[])
        assert binding.members == []

    def test_binding_multiple_members(self):
        """Test binding with multiple members."""
        members = [
            "user:user1@example.com",
            "user:user2@example.com",
            "serviceAccount:sa@project.iam.gserviceaccount.com",
        ]
        binding = Binding(role="roles/editor", members=members)
        assert len(binding.members) == 3

    def test_binding_missing_role(self):
        """Test that binding requires role."""
        with pytest.raises(ValidationError):
            Binding(members=["user:test@example.com"])

    def test_binding_missing_members(self):
        """Test that binding requires members."""
        with pytest.raises(ValidationError):
            Binding(role="roles/viewer")


class TestPolicy:
    """Tests for the Policy model."""

    def test_policy_creation_valid(self):
        """Test creating a valid policy."""
        bindings = [Binding(role="roles/viewer", members=["user:test@example.com"])]
        policy = Policy(bindings=bindings)
        assert len(policy.bindings) == 1
        assert policy.version == 1
        assert policy.etag is None

    def test_policy_with_etag_and_version(self):
        """Test policy with etag and version."""
        bindings = [Binding(role="roles/owner", members=["user:admin@example.com"])]
        policy = Policy(bindings=bindings, etag="BwXhFM7aN_k=", version=3)
        assert policy.etag == "BwXhFM7aN_k="
        assert policy.version == 3

    def test_policy_empty_bindings(self):
        """Test policy with no bindings."""
        policy = Policy(bindings=[])
        assert policy.bindings == []

    def test_policy_multiple_bindings(self):
        """Test policy with multiple bindings."""
        bindings = [
            Binding(role="roles/viewer", members=["user:viewer@example.com"]),
            Binding(role="roles/editor", members=["user:editor@example.com"]),
            Binding(role="roles/owner", members=["user:owner@example.com"]),
        ]
        policy = Policy(bindings=bindings)
        assert len(policy.bindings) == 3

    def test_policy_missing_bindings(self):
        """Test that policy requires bindings."""
        with pytest.raises(ValidationError):
            Policy()

    def test_policy_serialization(self):
        """Test policy can be serialized to dict."""
        bindings = [Binding(role="roles/viewer", members=["user:test@example.com"])]
        policy = Policy(bindings=bindings, etag="test-etag")
        policy_dict = policy.model_dump()

        assert "bindings" in policy_dict
        assert "etag" in policy_dict
        assert "version" in policy_dict
        assert policy_dict["etag"] == "test-etag"


class TestFinding:
    """Tests for the Finding model."""

    def test_finding_creation_valid(self):
        """Test creating a valid finding."""
        finding = Finding(
            id="RISKY_ROLE", severity="HIGH", description="Role 'roles/owner' is too permissive"
        )
        assert finding.id == "RISKY_ROLE"
        assert finding.severity == "HIGH"
        assert finding.resource == "project-policy"

    def test_finding_all_severities(self):
        """Test all valid severity levels."""
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        for severity in severities:
            finding = Finding(id="TEST", severity=severity, description="Test finding")
            assert finding.severity == severity

    def test_finding_invalid_severity(self):
        """Test that invalid severity raises error."""
        with pytest.raises(ValidationError):
            Finding(id="TEST", severity="INVALID", description="Test")

    def test_finding_with_details(self):
        """Test finding with details."""
        details = {"role": "roles/owner", "members": ["user:admin@example.com"]}
        finding = Finding(id="RISKY_ROLE", severity="HIGH", description="Test", details=details)
        assert finding.details == details

    def test_finding_with_remediation(self):
        """Test finding with remediation steps."""
        finding = Finding(
            id="WILDCARD_ACCESS",
            severity="CRITICAL",
            description="Public access detected",
            remediation="Remove allUsers from IAM policy",
        )
        assert finding.remediation == "Remove allUsers from IAM policy"

    def test_finding_custom_resource(self):
        """Test finding with custom resource."""
        finding = Finding(
            id="TEST",
            severity="LOW",
            description="Test",
            resource="projects/my-project/buckets/my-bucket",
        )
        assert finding.resource == "projects/my-project/buckets/my-bucket"

    def test_finding_missing_required_fields(self):
        """Test that finding requires id, severity, and description."""
        with pytest.raises(ValidationError):
            Finding(severity="HIGH", description="Test")

        with pytest.raises(ValidationError):
            Finding(id="TEST", description="Test")

        with pytest.raises(ValidationError):
            Finding(id="TEST", severity="HIGH")


class TestScenarioCheck:
    """Tests for the ScenarioCheck model."""

    def test_scenario_check_creation(self):
        """Test creating a scenario check."""
        check = ScenarioCheck(name="Check IAM Policy", description="Verify no public access")
        assert check.name == "Check IAM Policy"
        assert check.status == "PENDING"
        assert check.details is None

    def test_scenario_check_with_status(self):
        """Test scenario check with different statuses."""
        statuses = ["PENDING", "PASS", "FAIL", "ERROR"]
        for status in statuses:
            check = ScenarioCheck(name="Test", description="Test check", status=status)
            assert check.status == status

    def test_scenario_check_with_details(self):
        """Test scenario check with details."""
        check = ScenarioCheck(
            name="Test", description="Test check", status="FAIL", details="Found 3 violations"
        )
        assert check.details == "Found 3 violations"


class TestScenarioResult:
    """Tests for the ScenarioResult model."""

    def test_scenario_result_creation(self):
        """Test creating a scenario result."""
        checks = [
            ScenarioCheck(name="Check 1", description="First check"),
            ScenarioCheck(name="Check 2", description="Second check"),
        ]
        result = ScenarioResult(
            scenario_name="Privilege Escalation Test",
            checks=checks,
            actions_required=["Fix IAM policy", "Review service accounts"],
        )
        assert result.scenario_name == "Privilege Escalation Test"
        assert len(result.checks) == 2
        assert len(result.actions_required) == 2

    def test_scenario_result_empty_checks(self):
        """Test scenario result with no checks."""
        result = ScenarioResult(scenario_name="Test", checks=[], actions_required=[])
        assert result.checks == []
        assert result.actions_required == []

    def test_scenario_result_serialization(self):
        """Test scenario result can be serialized."""
        checks = [ScenarioCheck(name="Test", description="Test check", status="PASS")]
        result = ScenarioResult(
            scenario_name="Test Scenario", checks=checks, actions_required=["Action 1"]
        )
        result_dict = result.model_dump()

        assert "scenario_name" in result_dict
        assert "checks" in result_dict
        assert "actions_required" in result_dict
        assert result_dict["scenario_name"] == "Test Scenario"


class TestModelIntegration:
    """Integration tests for models working together."""

    def test_policy_with_findings_workflow(self):
        """Test complete workflow from policy to findings."""
        # Create a policy
        bindings = [
            Binding(role="roles/owner", members=["allUsers"]),
            Binding(role="roles/viewer", members=["user:safe@example.com"]),
        ]
        policy = Policy(bindings=bindings)

        # Create findings based on policy
        findings = []
        for binding in policy.bindings:
            if "allUsers" in binding.members:
                findings.append(
                    Finding(
                        id="WILDCARD_ACCESS",
                        severity="CRITICAL",
                        description=f"Public access on {binding.role}",
                        details={"role": binding.role},
                    )
                )

        assert len(findings) == 1
        assert findings[0].severity == "CRITICAL"

    def test_scenario_result_with_multiple_checks(self):
        """Test scenario result with various check statuses."""
        checks = [
            ScenarioCheck(name="Check 1", description="Test 1", status="PASS"),
            ScenarioCheck(name="Check 2", description="Test 2", status="FAIL"),
            ScenarioCheck(name="Check 3", description="Test 3", status="PENDING"),
        ]
        result = ScenarioResult(
            scenario_name="Comprehensive Test", checks=checks, actions_required=["Fix check 2"]
        )

        passed = [c for c in result.checks if c.status == "PASS"]
        failed = [c for c in result.checks if c.status == "FAIL"]

        assert len(passed) == 1
        assert len(failed) == 1
