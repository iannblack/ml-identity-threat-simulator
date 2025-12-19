from __future__ import annotations

import logging
from typing import Any

from src.core.config import AppConfig
from src.core.models import AwsPolicy, AwsStatement, Finding

logger = logging.getLogger("iam-simulator")


class AwsAuditor:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig()

    def audit_policy(self, policy: AwsPolicy) -> list[Finding]:
        findings: list[Finding] = []

        for stmt in policy.Statement:
            # Only care about Allow statements for risky permissions
            if stmt.Effect != "Allow":
                continue

            findings.extend(self._check_unrestricted_admin(stmt))
            findings.extend(self._check_public_access(stmt))

        return findings

    def _check_unrestricted_admin(self, stmt: AwsStatement) -> list[Finding]:
        findings = []
        actions = stmt.Action if isinstance(stmt.Action, list) else [stmt.Action]
        resources = stmt.Resource if isinstance(stmt.Resource, list) else [stmt.Resource]

        # Normalize actions and resources
        actions_set = set(actions)
        resources_set = set(resources) if resources else set()

        # Check for AdministratorAccess (Action: * and Resource: *)
        if "*" in actions_set and "*" in resources_set:
             findings.append(
                Finding(
                    id="AWS_UNRESTRICTED_ADMIN",
                    severity="CRITICAL",
                    description="Policy grants full administrative access (Action:* on Resource:*)",
                    resource="aws_policy",
                    details={"statement": stmt.model_dump()},
                    remediation="Restrict actions and resources to least privilege.",
                )
            )

        return findings

    def _check_public_access(self, stmt: AwsStatement) -> list[Finding]:
        findings = []
        if not stmt.Principal:
            return findings

        # Check for Principal: "*" / {"AWS": "*"}
        is_public = False
        if stmt.Principal == "*":
             is_public = True
        elif isinstance(stmt.Principal, dict):
             if stmt.Principal.get("AWS") == "*":
                 is_public = True
        
        if is_public:
            findings.append(
                Finding(
                    id="AWS_PUBLIC_ACCESS",
                    severity="CRITICAL",
                    description="Policy allows public access via Principal: *",
                    resource="aws_policy",
                    details={"statement": stmt.model_dump()},
                    remediation="Specify explicit AWS accounts or users in Principal.",
                )
            )
        
        return findings
