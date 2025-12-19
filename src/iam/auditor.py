from typing import List
from src.core.models import Policy, Finding
from src.core.config import AppConfig

class IAMAuditor:
    def __init__(self, config: AppConfig):
        self.config = config

    def audit_policy(self, policy: Policy) -> List[Finding]:
        findings = []
        for binding in policy.bindings:
            # Check 1: Risky Roles
            if binding.role in self.config.risky_roles:
                findings.append(Finding(
                    id="RISKY_ROLE",
                    severity="HIGH",
                    description=f"Role '{binding.role}' is considered too permissive.",
                    details={"role": binding.role, "members": binding.members},
                    remediation=f"Consider downgrading to a less privileged role."
                ))

            # Check 2: Wildcard Access
            for member in binding.members:
                if member in self.config.wildcard_members or member.endswith("allUsers") or member.endswith("allAuthenticatedUsers"):
                    findings.append(Finding(
                        id="WILDCARD_ACCESS",
                        severity="CRITICAL",
                        description=f"Public access detected via '{member}' on role '{binding.role}'.",
                        details={"role": binding.role, "member": member},
                        remediation="Remove public access immediately."
                    ))
                
                # Check 3: Mixed Analysis (e.g. Service Account with Owner)
                if member.startswith("serviceAccount:") and binding.role in ["roles/owner", "roles/editor"]:
                     findings.append(Finding(
                        id="SA_HIGH_PRIVILEGE",
                        severity="MEDIUM",
                        description=f"Service Account '{member}' has broad privileges '{binding.role}'.",
                        details={"role": binding.role, "member": member},
                        remediation="Apply Least Privilege principle."
                    ))
                    
        return findings
