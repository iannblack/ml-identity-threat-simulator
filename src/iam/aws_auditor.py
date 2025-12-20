from __future__ import annotations

import logging

from src.core.config import AppConfig
from src.core.models import AwsPolicy, AwsStatement, Finding

logger = logging.getLogger("iam-simulator")


class AwsAuditor:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig(risky_roles=[], wildcard_members=[])

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
        findings: list[Finding] = []

        # Action and Resource are required fields per AWS spec but could be None in loose models
        stmt_actions = stmt.Action or []
        stmt_resources = stmt.Resource or []

        actions = stmt_actions if isinstance(stmt_actions, list) else [stmt_actions]
        resources = stmt_resources if isinstance(stmt_resources, list) else [stmt_resources]

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
        findings: list[Finding] = []
        if not stmt.Principal:
            return findings

        # Check for Principal: "*" / {"AWS": "*"}
        if stmt.Principal == "*" or (
            isinstance(stmt.Principal, dict) and stmt.Principal.get("AWS") == "*"
        ):
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
