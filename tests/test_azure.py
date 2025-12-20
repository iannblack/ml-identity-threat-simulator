import json
import os
import tempfile

import pytest

from src.core.config import AppConfig
from src.core.models import AzureRoleDefinition
from src.iam.azure_auditor import AzureAuditor
from src.iam.azure_parsers import load_azure_role_from_json


class TestAzureParser:
    def test_load_valid_role(self):
        role_data = {
            "roleName": "MyRole",
            "description": "Custom role",
            "actions": ["Microsoft.Compute/*/read"],
            "notActions": [],
            "assignableScopes": ["/subscriptions/123"],
            "isCustom": True,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(role_data, f)
            temp_path = f.name

        try:
            role = load_azure_role_from_json(temp_path)
            assert isinstance(role, AzureRoleDefinition)
            assert role.RoleName == "MyRole"
            assert role.IsCustom is True
            assert "Microsoft.Compute/*/read" in role.Actions
        finally:
            os.unlink(temp_path)

    def test_load_role_from_list(self):
        """Test loading a role when the JSON is a list (e.g. from 'az role definition list')."""
        role_data = [
            {
                "roleName": "ListRole",
                "actions": ["*"],
                "assignableScopes": ["/"],
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(role_data, f)
            temp_path = f.name

        try:
            role = load_azure_role_from_json(temp_path)
            assert role.RoleName == "ListRole"
            assert "*" in role.Actions
        finally:
            os.unlink(temp_path)

    def test_load_role_with_properties_wrapper(self):
        role_data = {
            "properties": {
                "roleName": "WrappedRole",
                "permissions": [{"actions": ["*"], "notActions": []}],
                "assignableScopes": ["/"],
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(role_data, f)
            temp_path = f.name

        try:
            role = load_azure_role_from_json(temp_path)
            assert role.RoleName == "WrappedRole"
            assert "*" in role.Actions
        finally:
            os.unlink(temp_path)


class TestAzureAuditor:
    @pytest.fixture
    def auditor(self):
        config = AppConfig(risky_roles=[], wildcard_members=[])
        return AzureAuditor(config=config)

    def test_detect_admin_access_star(self, auditor):
        role = AzureRoleDefinition(roleName="AdminRole", actions=["*"], assignableScopes=["/subscriptions/123"])
        findings = auditor.audit_policy(role)
        assert len(findings) == 1
        assert findings[0].id == "AZURE_ADMIN_ACCESS"

    def test_detect_admin_access_wildcard_all(self, auditor):
        role = AzureRoleDefinition(
            roleName="AdminRole",
            actions=["Microsoft.Authorization/*", "*/*"],
            assignableScopes=["/subscriptions/123"],
        )
        findings = auditor.audit_policy(role)
        assert any(f.id == "AZURE_ADMIN_ACCESS" for f in findings)

    def test_detect_broad_scope_root(self, auditor):
        role = AzureRoleDefinition(
            roleName="CustomRoot",
            isCustom=True,
            actions=["Microsoft.Compute/virtualMachines/read"],
            assignableScopes=["/"],
        )
        findings = auditor.audit_policy(role)
        assert len(findings) == 1
        assert findings[0].id == "AZURE_BROAD_SCOPE"

    def test_detect_broad_scope_subscription(self, auditor):
        role = AzureRoleDefinition(
            roleName="CustomSub",
            isCustom=True,
            actions=["Microsoft.Compute/virtualMachines/read"],
            assignableScopes=["/subscriptions/12345678-1234-1234-1234-123456789012"],
        )
        findings = auditor.audit_policy(role)
        assert len(findings) == 1
        assert findings[0].id == "AZURE_BROAD_SCOPE"

    def test_safe_role(self, auditor):
        role = AzureRoleDefinition(
            roleName="SafeRole",
            isCustom=True,
            actions=["Microsoft.Compute/virtualMachines/read"],
            assignableScopes=["/subscriptions/123/resourceGroups/my-rg"],
        )
        findings = auditor.audit_policy(role)
        assert len(findings) == 0

    def test_builtin_role_ignore_scope(self, auditor):
        """Built-in roles often have broad scopes but we can't change them, so usually ignore scope check or mark as info."""
        # Our logic currently only checks IsCustom=True for broad scope
        role = AzureRoleDefinition(roleName="Owner", isCustom=False, actions=["*"], assignableScopes=["/"])
        findings = auditor.audit_policy(role)
        # Should detect ADMIN ACCESS but NOT BROAD SCOPE because IsCustom=False
        ids = [f.id for f in findings]
        assert "AZURE_ADMIN_ACCESS" in ids
        assert "AZURE_BROAD_SCOPE" not in ids
