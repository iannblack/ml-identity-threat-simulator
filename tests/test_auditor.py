"""
Comprehensive tests for iam.auditor module.
Tests IAM policy auditing logic, finding generation, and all security checks.
"""

import pytest

from src.core.config import AppConfig
from src.core.models import Binding, Policy
from src.iam.auditor import IAMAuditor


class TestIAMAuditorInit:
    """Tests for IAMAuditor initialization."""

    def test_auditor_creation(self):
        """Test creating an auditor instance."""
        config = AppConfig(risky_roles=["roles/owner"], wildcard_members=["allUsers"])
        auditor = IAMAuditor(config)
        assert auditor.config == config

    def test_auditor_with_custom_config(self):
        """Test auditor with custom configuration."""
        config = AppConfig(
            risky_roles=["roles/owner", "roles/editor", "roles/admin"],
            wildcard_members=["allUsers", "allAuthenticatedUsers", "domain:public.com"],
        )
        auditor = IAMAuditor(config)
        assert len(auditor.config.risky_roles) == 3
        assert len(auditor.config.wildcard_members) == 3


class TestRiskyRoleDetection:
    """Tests for risky role detection."""

    @pytest.fixture
    def auditor(self):
        config = AppConfig(
            risky_roles=["roles/owner", "roles/editor", "roles/bigquery.admin"],
            wildcard_members=["allUsers"],
        )
        return IAMAuditor(config)

    def test_detect_owner_role(self, auditor):
        """Test detection of owner role."""
        policy = Policy(bindings=[Binding(role="roles/owner", members=["user:admin@example.com"])])
        findings = auditor.audit_policy(policy)

        assert len(findings) == 1
        assert findings[0].id == "RISKY_ROLE"
        assert findings[0].severity == "HIGH"
        assert "roles/owner" in findings[0].description

    def test_detect_editor_role(self, auditor):
        """Test detection of editor role."""
        policy = Policy(
            bindings=[Binding(role="roles/editor", members=["user:editor@example.com"])]
        )
        findings = auditor.audit_policy(policy)

        assert len(findings) == 1
        assert findings[0].id == "RISKY_ROLE"
        assert "roles/editor" in findings[0].description

    def test_detect_bigquery_admin(self, auditor):
        """Test detection of BigQuery admin role."""
        policy = Policy(
            bindings=[Binding(role="roles/bigquery.admin", members=["user:bq@example.com"])]
        )
        findings = auditor.audit_policy(policy)

        assert len(findings) == 1
        assert findings[0].id == "RISKY_ROLE"

    def test_safe_role_no_finding(self, auditor):
        """Test that safe roles don't generate findings."""
        policy = Policy(
            bindings=[Binding(role="roles/viewer", members=["user:viewer@example.com"])]
        )
        findings = auditor.audit_policy(policy)

        assert len(findings) == 0

    def test_multiple_risky_roles(self, auditor):
        """Test detection of multiple risky roles."""
        policy = Policy(
            bindings=[
                Binding(role="roles/owner", members=["user:owner@example.com"]),
                Binding(role="roles/editor", members=["user:editor@example.com"]),
                Binding(role="roles/viewer", members=["user:viewer@example.com"]),
            ]
        )
        findings = auditor.audit_policy(policy)

        # Should find 2 risky roles (owner and editor)
        risky_findings = [f for f in findings if f.id == "RISKY_ROLE"]
        assert len(risky_findings) == 2


class TestWildcardAccessDetection:
    """Tests for wildcard/public access detection."""

    @pytest.fixture
    def auditor(self):
        config = AppConfig(
            risky_roles=["roles/owner"], wildcard_members=["allUsers", "allAuthenticatedUsers"]
        )
        return IAMAuditor(config)

    def test_detect_all_users(self, auditor):
        """Test detection of allUsers."""
        policy = Policy(bindings=[Binding(role="roles/viewer", members=["allUsers"])])
        findings = auditor.audit_policy(policy)

        assert len(findings) == 1
        assert findings[0].id == "WILDCARD_ACCESS"
        assert findings[0].severity == "CRITICAL"
        assert "allUsers" in findings[0].description

    def test_detect_all_authenticated_users(self, auditor):
        """Test detection of allAuthenticatedUsers."""
        policy = Policy(bindings=[Binding(role="roles/viewer", members=["allAuthenticatedUsers"])])
        findings = auditor.audit_policy(policy)

        assert len(findings) == 1
        assert findings[0].id == "WILDCARD_ACCESS"
        assert "allAuthenticatedUsers" in findings[0].description

    def test_detect_member_ending_with_all_users(self, auditor):
        """Test detection of members ending with allUsers."""
        policy = Policy(bindings=[Binding(role="roles/viewer", members=["domain:allUsers"])])
        findings = auditor.audit_policy(policy)

        assert len(findings) == 1
        assert findings[0].id == "WILDCARD_ACCESS"

    def test_detect_member_ending_with_all_authenticated_users(self, auditor):
        """Test detection of members ending with allAuthenticatedUsers."""
        policy = Policy(
            bindings=[Binding(role="roles/viewer", members=["domain:allAuthenticatedUsers"])]
        )
        findings = auditor.audit_policy(policy)

        assert len(findings) == 1
        assert findings[0].id == "WILDCARD_ACCESS"

    def test_multiple_wildcard_members(self, auditor):
        """Test detection of multiple wildcard members in one binding."""
        policy = Policy(
            bindings=[
                Binding(
                    role="roles/viewer",
                    members=["allUsers", "user:safe@example.com", "allAuthenticatedUsers"],
                )
            ]
        )
        findings = auditor.audit_policy(policy)

        wildcard_findings = [f for f in findings if f.id == "WILDCARD_ACCESS"]
        assert len(wildcard_findings) == 2

    def test_no_wildcard_safe_members(self, auditor):
        """Test that normal members don't trigger wildcard detection."""
        policy = Policy(
            bindings=[
                Binding(
                    role="roles/viewer",
                    members=[
                        "user:user1@example.com",
                        "user:user2@example.com",
                        "serviceAccount:sa@project.iam.gserviceaccount.com",
                    ],
                )
            ]
        )
        findings = auditor.audit_policy(policy)

        wildcard_findings = [f for f in findings if f.id == "WILDCARD_ACCESS"]
        assert len(wildcard_findings) == 0


class TestServiceAccountHighPrivilege:
    """Tests for service account high privilege detection."""

    @pytest.fixture
    def auditor(self):
        config = AppConfig(
            risky_roles=["roles/owner", "roles/editor"], wildcard_members=["allUsers"]
        )
        return IAMAuditor(config)

    def test_detect_sa_with_owner(self, auditor):
        """Test detection of service account with owner role."""
        policy = Policy(
            bindings=[
                Binding(
                    role="roles/owner",
                    members=["serviceAccount:sa@project.iam.gserviceaccount.com"],
                )
            ]
        )
        findings = auditor.audit_policy(policy)

        sa_findings = [f for f in findings if f.id == "SA_HIGH_PRIVILEGE"]
        assert len(sa_findings) == 1
        assert sa_findings[0].severity == "MEDIUM"

    def test_detect_sa_with_editor(self, auditor):
        """Test detection of service account with editor role."""
        policy = Policy(
            bindings=[
                Binding(
                    role="roles/editor",
                    members=["serviceAccount:editor-sa@project.iam.gserviceaccount.com"],
                )
            ]
        )
        findings = auditor.audit_policy(policy)

        sa_findings = [f for f in findings if f.id == "SA_HIGH_PRIVILEGE"]
        assert len(sa_findings) == 1

    def test_sa_with_safe_role_no_finding(self, auditor):
        """Test that SA with safe role doesn't generate SA_HIGH_PRIVILEGE finding."""
        policy = Policy(
            bindings=[
                Binding(
                    role="roles/viewer",
                    members=["serviceAccount:viewer-sa@project.iam.gserviceaccount.com"],
                )
            ]
        )
        findings = auditor.audit_policy(policy)

        sa_findings = [f for f in findings if f.id == "SA_HIGH_PRIVILEGE"]
        assert len(sa_findings) == 0

    def test_user_with_owner_no_sa_finding(self, auditor):
        """Test that regular user with owner doesn't trigger SA finding."""
        policy = Policy(bindings=[Binding(role="roles/owner", members=["user:admin@example.com"])])
        findings = auditor.audit_policy(policy)

        sa_findings = [f for f in findings if f.id == "SA_HIGH_PRIVILEGE"]
        assert len(sa_findings) == 0

    def test_multiple_sa_high_privilege(self, auditor):
        """Test detection of multiple SAs with high privileges."""
        policy = Policy(
            bindings=[
                Binding(
                    role="roles/owner",
                    members=[
                        "serviceAccount:sa1@project.iam.gserviceaccount.com",
                        "serviceAccount:sa2@project.iam.gserviceaccount.com",
                    ],
                )
            ]
        )
        findings = auditor.audit_policy(policy)

        sa_findings = [f for f in findings if f.id == "SA_HIGH_PRIVILEGE"]
        assert len(sa_findings) == 2


class TestCombinedFindings:
    """Tests for policies that trigger multiple finding types."""

    @pytest.fixture
    def auditor(self):
        config = AppConfig(
            risky_roles=["roles/owner", "roles/editor"],
            wildcard_members=["allUsers", "allAuthenticatedUsers"],
        )
        return IAMAuditor(config)

    def test_risky_role_with_wildcard(self, auditor):
        """Test policy with both risky role and wildcard access."""
        policy = Policy(bindings=[Binding(role="roles/owner", members=["allUsers"])])
        findings = auditor.audit_policy(policy)

        # Should generate both RISKY_ROLE and WILDCARD_ACCESS
        assert len(findings) == 2
        finding_ids = {f.id for f in findings}
        assert "RISKY_ROLE" in finding_ids
        assert "WILDCARD_ACCESS" in finding_ids

    def test_risky_role_with_sa(self, auditor):
        """Test risky role assigned to service account."""
        policy = Policy(
            bindings=[
                Binding(
                    role="roles/owner",
                    members=["serviceAccount:sa@project.iam.gserviceaccount.com"],
                )
            ]
        )
        findings = auditor.audit_policy(policy)

        # Should generate both RISKY_ROLE and SA_HIGH_PRIVILEGE
        assert len(findings) == 2
        finding_ids = {f.id for f in findings}
        assert "RISKY_ROLE" in finding_ids
        assert "SA_HIGH_PRIVILEGE" in finding_ids

    def test_all_three_findings(self, auditor):
        """Test policy that triggers all three finding types."""
        policy = Policy(
            bindings=[
                Binding(
                    role="roles/owner",
                    members=["allUsers", "serviceAccount:sa@project.iam.gserviceaccount.com"],
                )
            ]
        )
        findings = auditor.audit_policy(policy)

        # Should generate RISKY_ROLE, WILDCARD_ACCESS, and SA_HIGH_PRIVILEGE
        assert len(findings) == 3
        finding_ids = {f.id for f in findings}
        assert "RISKY_ROLE" in finding_ids
        assert "WILDCARD_ACCESS" in finding_ids
        assert "SA_HIGH_PRIVILEGE" in finding_ids

    def test_complex_policy_multiple_bindings(self, auditor):
        """Test complex policy with multiple bindings and findings."""
        policy = Policy(
            bindings=[
                Binding(role="roles/owner", members=["allUsers"]),
                Binding(
                    role="roles/editor",
                    members=["serviceAccount:sa@project.iam.gserviceaccount.com"],
                ),
                Binding(role="roles/viewer", members=["user:safe@example.com"]),
                Binding(role="roles/storage.admin", members=["allAuthenticatedUsers"]),
            ]
        )
        findings = auditor.audit_policy(policy)

        # Multiple findings expected
        assert len(findings) > 0

        risky_role_findings = [f for f in findings if f.id == "RISKY_ROLE"]
        wildcard_findings = [f for f in findings if f.id == "WILDCARD_ACCESS"]
        sa_findings = [f for f in findings if f.id == "SA_HIGH_PRIVILEGE"]

        assert len(risky_role_findings) >= 2  # owner and editor
        assert len(wildcard_findings) >= 2  # allUsers and allAuthenticatedUsers
        assert len(sa_findings) >= 1  # SA with editor


class TestEmptyAndEdgeCases:
    """Tests for empty policies and edge cases."""

    @pytest.fixture
    def auditor(self):
        config = AppConfig(risky_roles=["roles/owner"], wildcard_members=["allUsers"])
        return IAMAuditor(config)

    def test_empty_policy(self, auditor):
        """Test auditing empty policy."""
        policy = Policy(bindings=[])
        findings = auditor.audit_policy(policy)
        assert len(findings) == 0

    def test_binding_with_empty_members(self, auditor):
        """Test binding with no members."""
        policy = Policy(bindings=[Binding(role="roles/owner", members=[])])
        findings = auditor.audit_policy(policy)

        # Should still detect risky role
        risky_findings = [f for f in findings if f.id == "RISKY_ROLE"]
        assert len(risky_findings) == 1

    def test_safe_policy_no_findings(self, auditor):
        """Test completely safe policy generates no findings."""
        policy = Policy(
            bindings=[
                Binding(role="roles/viewer", members=["user:viewer@example.com"]),
                Binding(role="roles/logging.viewer", members=["user:logs@example.com"]),
            ]
        )
        findings = auditor.audit_policy(policy)
        assert len(findings) == 0


class TestFindingDetails:
    """Tests for finding details and metadata."""

    @pytest.fixture
    def auditor(self):
        config = AppConfig(risky_roles=["roles/owner"], wildcard_members=["allUsers"])
        return IAMAuditor(config)

    def test_risky_role_finding_details(self, auditor):
        """Test that risky role finding has correct details."""
        policy = Policy(bindings=[Binding(role="roles/owner", members=["user:admin@example.com"])])
        findings = auditor.audit_policy(policy)

        finding = findings[0]
        assert finding.details is not None
        assert "role" in finding.details
        assert "members" in finding.details
        assert finding.details["role"] == "roles/owner"

    def test_wildcard_finding_details(self, auditor):
        """Test that wildcard finding has correct details."""
        policy = Policy(bindings=[Binding(role="roles/viewer", members=["allUsers"])])
        findings = auditor.audit_policy(policy)

        finding = findings[0]
        assert finding.details is not None
        assert "role" in finding.details
        assert "member" in finding.details
        assert finding.details["member"] == "allUsers"

    def test_sa_finding_details(self, auditor):
        """Test that SA finding has correct details."""
        policy = Policy(
            bindings=[
                Binding(
                    role="roles/owner",
                    members=["serviceAccount:sa@project.iam.gserviceaccount.com"],
                )
            ]
        )
        findings = auditor.audit_policy(policy)

        sa_finding = [f for f in findings if f.id == "SA_HIGH_PRIVILEGE"][0]
        assert sa_finding.details is not None
        assert "role" in sa_finding.details
        assert "member" in sa_finding.details

    def test_finding_has_remediation(self, auditor):
        """Test that findings include remediation advice."""
        policy = Policy(bindings=[Binding(role="roles/owner", members=["allUsers"])])
        findings = auditor.audit_policy(policy)

        for finding in findings:
            assert finding.remediation is not None
            assert len(finding.remediation) > 0
