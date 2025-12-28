"""Feature extraction from IAM policies for ML models."""

import numpy as np

from src.core.models import AwsPolicy, AzureRoleDefinition, Policy


class PolicyFeatureExtractor:
    """Extract numerical features from IAM policies for ML analysis."""

    def __init__(self) -> None:
        """Initialize the feature extractor."""
        self.risky_roles = {
            "roles/owner",
            "roles/editor",
            "roles/iam.securityAdmin",
            "roles/resourcemanager.organizationAdmin",
            "roles/compute.admin",
            "roles/storage.admin",
        }
        self.risky_aws_actions = {
            "iam:*",
            "s3:*",
            "ec2:*",
            "lambda:*",
            "iam:CreateUser",
            "iam:AttachUserPolicy",
            "iam:PutUserPolicy",
        }
        self.risky_azure_actions = {
            "*",
            "Microsoft.Authorization/*",
            "Microsoft.Compute/*",
            "Microsoft.Storage/*",
        }

    def extract_gcp_features(self, policy: Policy) -> dict[str, float]:
        """Extract features from a GCP IAM policy."""
        features: dict[str, float] = {}

        # Basic counts
        features["num_bindings"] = float(len(policy.bindings))
        total_members = sum(len(b.members) for b in policy.bindings)
        features["total_members"] = float(total_members)
        features["avg_members_per_binding"] = (
            total_members / len(policy.bindings) if policy.bindings else 0.0
        )

        # Risky role detection
        risky_count = sum(1 for b in policy.bindings if b.role in self.risky_roles)
        features["risky_role_count"] = float(risky_count)
        features["risky_role_ratio"] = (
            risky_count / len(policy.bindings) if policy.bindings else 0.0
        )

        # Wildcard member detection (allUsers, allAuthenticatedUsers)
        wildcard_count = sum(
            1
            for b in policy.bindings
            for m in b.members
            if m in ("allUsers", "allAuthenticatedUsers")
        )
        features["wildcard_member_count"] = float(wildcard_count)

        # Service account features
        sa_count = sum(1 for b in policy.bindings for m in b.members if ".gserviceaccount.com" in m)
        features["service_account_count"] = float(sa_count)
        features["service_account_ratio"] = sa_count / total_members if total_members > 0 else 0.0

        # Conditional bindings
        conditional_count = sum(1 for b in policy.bindings if b.condition is not None)
        features["conditional_binding_count"] = float(conditional_count)
        features["conditional_binding_ratio"] = (
            conditional_count / len(policy.bindings) if policy.bindings else 0.0
        )

        # Role diversity (unique roles)
        unique_roles = len({b.role for b in policy.bindings})
        features["unique_role_count"] = float(unique_roles)
        features["role_diversity"] = unique_roles / len(policy.bindings) if policy.bindings else 0.0

        return features

    def extract_aws_features(self, policy: AwsPolicy) -> dict[str, float]:
        """Extract features from an AWS IAM policy."""
        features: dict[str, float] = {}

        # Basic counts
        features["num_statements"] = float(len(policy.Statement))
        total_actions = sum(
            len(s.Action) if isinstance(s.Action, list) else 1 for s in policy.Statement
        )
        features["total_actions"] = float(total_actions)

        # Effect analysis
        allow_count = sum(1 for s in policy.Statement if s.Effect == "Allow")
        deny_count = sum(1 for s in policy.Statement if s.Effect == "Deny")
        features["allow_statement_count"] = float(allow_count)
        features["deny_statement_count"] = float(deny_count)
        features["allow_ratio"] = allow_count / len(policy.Statement) if policy.Statement else 0.0

        # Risky actions
        risky_count = 0
        for stmt in policy.Statement:
            actions = [stmt.Action] if isinstance(stmt.Action, str) else stmt.Action
            for action in actions:
                if action in self.risky_aws_actions or "*" in action:
                    risky_count += 1
                    break
        features["risky_action_count"] = float(risky_count)

        # Wildcard usage
        wildcard_count = sum(
            1
            for s in policy.Statement
            for a in ([s.Action] if isinstance(s.Action, str) else s.Action)
            if "*" in a
        )
        features["wildcard_action_count"] = float(wildcard_count)

        # Principal analysis
        wildcard_principal_count = 0
        for stmt in policy.Statement:
            if stmt.Principal == "*" or (
                isinstance(stmt.Principal, dict) and "*" in str(stmt.Principal)
            ):
                wildcard_principal_count += 1
        features["wildcard_principal_count"] = float(wildcard_principal_count)

        # Condition usage
        conditional_count = sum(1 for s in policy.Statement if s.Condition is not None)
        features["conditional_statement_count"] = float(conditional_count)
        features["conditional_statement_ratio"] = (
            conditional_count / len(policy.Statement) if policy.Statement else 0.0
        )

        return features

    def extract_azure_features(self, role: AzureRoleDefinition) -> dict[str, float]:
        """Extract features from an Azure role definition."""
        features: dict[str, float] = {}

        # Basic counts
        features["action_count"] = float(len(role.Actions))
        features["not_action_count"] = float(len(role.NotActions))
        features["data_action_count"] = float(len(role.DataActions))
        features["not_data_action_count"] = float(len(role.NotDataActions))
        features["assignable_scope_count"] = float(len(role.AssignableScopes))

        # Total permissions
        total_permissions = (
            len(role.Actions)
            + len(role.NotActions)
            + len(role.DataActions)
            + len(role.NotDataActions)
        )
        features["total_permissions"] = float(total_permissions)

        # Custom role indicator
        features["is_custom"] = 1.0 if role.IsCustom else 0.0

        # Risky action detection
        risky_count = sum(1 for a in role.Actions if a in self.risky_azure_actions or "*" in a)
        features["risky_action_count"] = float(risky_count)
        features["risky_action_ratio"] = risky_count / len(role.Actions) if role.Actions else 0.0

        # Wildcard usage
        wildcard_count = sum(1 for a in role.Actions if "*" in a)
        features["wildcard_action_count"] = float(wildcard_count)

        # Scope analysis
        features["has_subscription_scope"] = (
            1.0 if any("/subscriptions/" in s for s in role.AssignableScopes) else 0.0
        )
        features["has_management_group_scope"] = (
            1.0
            if any("/providers/Microsoft.Management/" in s for s in role.AssignableScopes)
            else 0.0
        )

        return features

    def extract_features(
        self, policy: Policy | AwsPolicy | AzureRoleDefinition
    ) -> dict[str, float]:
        """Extract features from any supported policy type."""
        if isinstance(policy, Policy):
            return self.extract_gcp_features(policy)
        if isinstance(policy, AwsPolicy):
            return self.extract_aws_features(policy)
        if isinstance(policy, AzureRoleDefinition):
            return self.extract_azure_features(policy)

        msg = f"Unsupported policy type: {type(policy)}"
        raise ValueError(msg)

    def features_to_vector(self, features: dict[str, float]) -> np.ndarray:
        """Convert feature dictionary to numpy array for ML models."""
        # Sort keys to ensure consistent ordering
        sorted_keys = sorted(features.keys())
        return np.array([features[k] for k in sorted_keys])

    def get_feature_names(self, policy_type: str = "gcp") -> list[str]:
        """Get feature names for a given policy type."""
        dummy_features = {}
        if policy_type == "gcp":
            from src.core.models import Binding

            dummy_policy = Policy(bindings=[Binding(role="test", members=[])])
            dummy_features = self.extract_gcp_features(dummy_policy)
        elif policy_type == "aws":
            from src.core.models import AwsStatement

            dummy_policy_aws = AwsPolicy(Statement=[AwsStatement(Effect="Allow", Action=[])])
            dummy_features = self.extract_aws_features(dummy_policy_aws)
        elif policy_type == "azure":
            dummy_role = AzureRoleDefinition(
                Name="dummy", roleName="dummy", description="dummy", isCustom=False
            )
            dummy_features = self.extract_azure_features(dummy_role)

        return sorted(dummy_features.keys())
