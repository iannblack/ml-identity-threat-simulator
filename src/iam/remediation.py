"""
Automated remediation workflows for IAM findings.
Generates CLI commands to fix detected security issues across GCP, AWS, and Azure.
"""

from abc import ABC, abstractmethod
import json

from src.core.models import Finding


class Remediator(ABC):
    """Abstract base class for cloud-specific remediators."""

    @abstractmethod
    def generate_remediation_command(self, finding: Finding) -> str | None:
        """Generate a single CLI command to remediate a finding."""
        pass

    def generate_script(self, findings: list[Finding], header: str = "#!/bin/bash") -> str:
        """Generate a complete shell script for multiple findings."""
        script_lines = [header, "", "# Auto-generated remediation script", ""]

        for finding in findings:
            cmd = self.generate_remediation_command(finding)
            if cmd:
                script_lines.append(f"# Remediation for: {finding.description} ({finding.id})")
                script_lines.append(cmd)
                script_lines.append("")
            else:
                script_lines.append(
                    f"# No automated remediation available for: {finding.description} ({finding.id})"
                )
                script_lines.append("")

        return "\n".join(script_lines)


class GcpRemediator(Remediator):
    """Generates gcloud commands for GCP remediation."""

    def __init__(self, project_id: str = "$PROJECT_ID"):
        self.project_id = project_id

    def generate_remediation_command(self, finding: Finding) -> str | None:
        details = finding.details or {}

        if finding.id == "WILDCARD_ACCESS":
            role = details.get("role")
            member = details.get("member")
            if role and member:
                return f"gcloud projects remove-iam-policy-binding {self.project_id} --member='{member}' --role='{role}'"

        elif finding.id == "RISKY_ROLE":
            role = details.get("role")
            members = details.get("members", [])
            cmds = []
            for member in members:
                cmds.append(
                    f"gcloud projects remove-iam-policy-binding {self.project_id} --member='{member}' --role='{role}'"
                )
            if cmds:
                return " && \\\n".join(cmds)

        elif finding.id == "SA_HIGH_PRIVILEGE":
            role = details.get("role")
            member = details.get("member")
            if role and member:
                return f"gcloud projects remove-iam-policy-binding {self.project_id} --member='{member}' --role='{role}'"

        return None


class AwsRemediator(Remediator):
    """Generates AWS CLI commands for remediation."""

    def generate_remediation_command(self, finding: Finding) -> str | None:
        details = finding.details or {}

        if finding.id == "AWS_PUBLIC_ACCESS":
            # This is tricky because the policy is inside a JSON file or inline.
            # We can't easily patch it with a single CLI command without knowing the policy name/ARN context.
            # However, we can provide a generic guidance command or a placeholder.
            return "# Manual intervention required: Update the policy to remove Principal: '*'"

        elif finding.id == "AWS_UNRESTRICTED_ADMIN":
            return "# Manual intervention required: Restrict Actions and Resources in the policy."

        return None


class AzureRemediator(Remediator):
    """Generates Azure CLI commands for remediation."""

    def generate_remediation_command(self, finding: Finding) -> str | None:
        details = finding.details or {}

        if finding.id == "AZURE_ADMIN_ACCESS":
            role_name = details.get("role")
            # Modifying a custom role definition
            if role_name:
                return f"# Update role definition for '{role_name}' to remove '*' actions.\n# az role definition update --name '{role_name}' --role-definition @new_role_def.json"

        elif finding.id == "AZURE_BROAD_SCOPE":
            role_name = details.get("role")
            if role_name:
                return f"# Update role '{role_name}' to reduce scope.\n# az role definition update --name '{role_name}' --role-definition @new_role_def.json"

        return None


class RemediationFactory:
    """Factory to get the correct remediator based on provider."""

    @staticmethod
    def get_remediator(provider: str) -> Remediator:
        if provider.lower() == "gcp":
            return GcpRemediator()
        elif provider.lower() == "aws":
            return AwsRemediator()
        elif provider.lower() == "azure":
            return AzureRemediator()
        else:
            raise ValueError(f"Unknown provider: {provider}")
