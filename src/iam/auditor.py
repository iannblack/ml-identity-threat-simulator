from src.core.config import AppConfig
from src.core.models import Finding, Policy


class IAMAuditor:
    def __init__(self, config: AppConfig):
        self.config = config

    def audit_policy(self, policy: Policy) -> list[Finding]:
        findings = []
        for binding in policy.bindings:
            # Check 1: Risky Roles
            if binding.role in self.config.risky_roles:
                findings.append(
                    Finding(
                        id="RISKY_ROLE",
                        severity="HIGH",
                        description=f"Role '{binding.role}' is considered too permissive.",
                        details={"role": binding.role, "members": binding.members},
                        remediation="Consider downgrading to a less privileged role.",
                        compliance=["CIS GCP 1.4", "NIST AC-6"],
                    )
                )

            # Check 2: Wildcard Access
            for member in binding.members:
                if member in self.config.wildcard_members or member.endswith(
                    ("allUsers", "allAuthenticatedUsers")
                ):
                    findings.append(
                        Finding(
                            id="WILDCARD_ACCESS",
                            severity="CRITICAL",
                            description=f"Public access detected via '{member}' on role '{binding.role}'.",
                            details={"role": binding.role, "member": member},
                            remediation="Remove public access immediately.",
                            compliance=["CIS GCP 1.2", "NIST AC-3"],
                        )
                    )

                # Check 3: Mixed Analysis (e.g. Service Account with Owner)
                if member.startswith("serviceAccount:") and binding.role in [
                    "roles/owner",
                    "roles/editor",
                ]:
                    findings.append(
                        Finding(
                            id="SA_HIGH_PRIVILEGE",
                            severity="MEDIUM",
                            description=f"Service Account '{member}' has broad privileges '{binding.role}'.",
                            details={"role": binding.role, "member": member},
                            remediation="Apply Least Privilege principle.",
                            compliance=["CIS GCP 1.5", "NIST AC-6"],
                        )
                    )

        return findings
