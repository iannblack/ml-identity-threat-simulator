"""
IaC Scanner module to audit extracted infrastructure resources.
"""

from typing import Any

from src.core.config import AppConfig
from src.core.models import Finding
from src.iam.auditor import IAMAuditor
from src.iam.aws_auditor import AwsAuditor

# from src.iam.azure_auditor import AzureAuditor  # Left for future implementation if parser supports it


class IacScanner:
    """Orchestrates auditing of IaC resources using existing IAM auditors."""

    def __init__(self, config: AppConfig):
        """
        Initialize scanner with application configuration.
        """
        self.config = config
        self.gcp_auditor = IAMAuditor(config)
        self.aws_auditor = AwsAuditor(config)
        # self.azure_auditor = AzureAuditor(config)

    def scan(self, resources: dict[str, list[Any]]) -> list[Finding]:
        """
        Scan extracted resources for security findings.

        Args:
            resources: Dictionary of lists of policy objects keyed by provider ('gcp', 'aws', etc.)
                       Output from TerraformParser.parse_plan().

        Returns:
            List of detected security findings.
        """
        findings: list[Finding] = []

        # GCP Scan
        for policy in resources.get("gcp", []):
            # Each item is a Policy object
            current_findings = self.gcp_auditor.audit_policy(policy)
            # Tag findings as IaC origin if needed, or rely on resource field
            for f in current_findings:
                f.resource = f"terraform:{f.resource}"
            findings.extend(current_findings)

        # AWS Scan
        for policy in resources.get("aws", []):
            # Each item is an AwsPolicy object
            current_findings = self.aws_auditor.audit_policy(policy)
            for f in current_findings:
                f.resource = f"terraform:{f.resource}"
            findings.extend(current_findings)

        return findings
