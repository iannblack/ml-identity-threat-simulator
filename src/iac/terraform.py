"""
Terraform plan parser for extracting IAM resources.
"""

import json
from typing import Any

from src.core.models import AwsPolicy, AwsStatement, Binding, Policy


class TerraformParser:
    """Parses Terraform JSON plans to extract IAM configurations."""

    def parse_plan(self, plan_path: str) -> dict[str, list[Any]]:
        """
        Parse a Terraform plan JSON file and extract converted IAM policies.

        Returns:
            Dictionary with keys 'gcp', 'aws', 'azure' containing lists of extracted policy objects.
        """
        with open(plan_path) as f:
            plan = json.load(f)

        results: dict[str, list[Any]] = {
            "gcp": [],
            "aws": [],
            "azure": [],
        }

        # Scan resource_changes for IAM resources
        for resource in plan.get("resource_changes", []):
            resource_type = resource.get("type", "")
            change = resource.get("change", {})
            actions = change.get("actions", [])

            # Skip deleted resources
            if "delete" in actions and len(actions) == 1:
                continue

            after = change.get("after", {})
            if not after:
                continue

            self._process_gcp_resource(resource_type, after, results["gcp"])
            self._process_aws_resource(resource_type, after, results["aws"])
            # Azure support can be added here

        return results

    def _process_gcp_resource(
        self, r_type: str, data: dict[str, Any], results: list[Policy]
    ) -> None:
        """Process GCP IAM resources."""
        # google_project_iam_binding
        if r_type == "google_project_iam_binding":
            role = data.get("role")
            members = data.get("members", [])
            if role and members:
                binding = Binding(role=role, members=members)
                # Terraform defines bindings individually, we wrap in a Policy
                results.append(Policy(bindings=[binding]))

        # google_project_iam_member
        elif r_type == "google_project_iam_member":
            role = data.get("role")
            member = data.get("member")
            if role and member:
                binding = Binding(role=role, members=[member])
                results.append(Policy(bindings=[binding]))

    def _process_aws_resource(
        self, r_type: str, data: dict[str, Any], results: list[AwsPolicy]
    ) -> None:
        """Process AWS IAM resources."""
        # aws_iam_policy (managed policy)
        if r_type == "aws_iam_policy":
            policy_json = data.get("policy")
            if policy_json:
                try:
                    policy_dict = json.loads(policy_json)
                    statements = []
                    raw_statements = policy_dict.get("Statement", [])
                    if isinstance(raw_statements, dict):
                        raw_statements = [raw_statements]

                    for stmt in raw_statements:
                        statements.append(
                            AwsStatement(
                                Effect=stmt.get("Effect", "Allow"),
                                Action=stmt.get("Action", []),
                                Resource=stmt.get("Resource", []),
                                Principal=stmt.get("Principal"),
                            )
                        )
                    results.append(AwsPolicy(Statement=statements))
                except json.JSONDecodeError:
                    pass  # Cannot parse policy document

        # aws_iam_role_policy (inline policy)
        elif r_type == "aws_iam_role_policy":
            policy_json = data.get("policy")
            if policy_json:
                try:
                    policy_dict = json.loads(policy_json)
                    statements = []
                    raw_statements = policy_dict.get("Statement", [])
                    if isinstance(raw_statements, dict):
                        raw_statements = [raw_statements]

                    for stmt in raw_statements:
                        statements.append(
                            AwsStatement(
                                Effect=stmt.get("Effect", "Allow"),
                                Action=stmt.get("Action", []),
                                Resource=stmt.get("Resource", []),
                                Principal=stmt.get("Principal"),
                            )
                        )
                    results.append(AwsPolicy(Statement=statements))
                except json.JSONDecodeError:
                    pass
