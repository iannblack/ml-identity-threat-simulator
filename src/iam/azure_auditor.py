from __future__ import annotations

import logging

from src.core.config import AppConfig
from src.core.models import AzureRoleDefinition, Finding

logger = logging.getLogger("iam-simulator")


class AzureAuditor:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig(risky_roles=[], wildcard_members=[])

    def audit_policy(self, role: AzureRoleDefinition) -> list[Finding]:
        findings: list[Finding] = []

        findings.extend(self._check_admin_access(role))
        findings.extend(self._check_broad_scope(role))

        return findings

    def _check_admin_access(self, role: AzureRoleDefinition) -> list[Finding]:
        findings: list[Finding] = []

        # Check for full admin access
        has_star_action = "*" in role.Actions
        # Also common pattern: Microsoft.Authorization/* or just */*
        has_wildcard_all = any(a == "*" or a.endswith("/*") for a in role.Actions)

        if has_star_action or has_wildcard_all:
            findings.append(
                Finding(
                    id="AZURE_ADMIN_ACCESS",
                    severity="CRITICAL",
                    description=f"Role '{role.RoleName}' has full admin access (Actions: *)",
                    resource="azure_role",
                    details={"role": role.RoleName, "actions": role.Actions},
                    remediation="Restrict actions to only necessary operations.",
                    compliance=["CIS Azure 1.23", "NIST AC-6"],
                )
            )

        return findings

    def _check_broad_scope(self, role: AzureRoleDefinition) -> list[Finding]:
        findings: list[Finding] = []

        # Only relevant for custom roles
        if not role.IsCustom:
            return findings

        # Check for root scope or subscription scope
        for scope in role.AssignableScopes:
            if scope == "/" or (scope.startswith("/subscriptions/") and len(scope.split("/")) == 3):
                findings.append(
                    Finding(
                        id="AZURE_BROAD_SCOPE",
                        severity="HIGH",
                        description=f"Custom Role '{role.RoleName}' is assignable at a broad scope ({scope})",
                        resource="azure_role",
                        details={"role": role.RoleName, "scope": scope},
                        remediation="Limit AssignableScopes to specific Resource Groups where possible.",
                        compliance=["CIS Azure 1.2", "NIST AC-3"],
                    )
                )

        return findings
