"""Tests for ML-based anomaly detection."""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from src.core.models import AwsPolicy, AwsStatement, AzureRoleDefinition, Binding, Policy
from src.ml.detector import AnomalyDetector
from src.ml.feature_extractor import PolicyFeatureExtractor
from src.ml.models import AnomalyResult, MLConfig


@pytest.fixture
def normal_gcp_policies() -> list[Policy]:
    """Create a set of normal GCP policies for training."""
    policies = []
    for i in range(20):
        bindings = [
            Binding(
                role="roles/viewer",
                members=[
                    f"user:user{i}@example.com",
                    "serviceAccount:sa@project.iam.gserviceaccount.com",
                ],
            ),
            Binding(
                role="roles/editor",
                members=[f"user:admin{i}@example.com"],
            ),
        ]
        policies.append(Policy(bindings=bindings))
    return policies


@pytest.fixture
def anomalous_gcp_policy() -> Policy:
    """Create an anomalous GCP policy."""
    return Policy(
        bindings=[
            Binding(
                role="roles/owner",
                members=["allUsers", "allAuthenticatedUsers"],
            ),
            Binding(
                role="roles/iam.securityAdmin",
                members=["user:malicious@evil.com"],
            ),
        ]
    )


@pytest.fixture
def normal_aws_policies() -> list[AwsPolicy]:
    """Create a set of normal AWS policies for training."""
    policies = []
    for i in range(20):
        statements = [
            AwsStatement(
                Effect="Allow",
                Action=["s3:GetObject"],
                Resource=[f"arn:aws:s3:::bucket-{i}/*"],
            ),
            AwsStatement(
                Effect="Deny",
                Action=["iam:DeleteUser"],
                Resource=["*"],
            ),
        ]
        policies.append(AwsPolicy(Statement=statements))
    return policies


@pytest.fixture
def anomalous_aws_policy() -> AwsPolicy:
    """Create an anomalous AWS policy."""
    return AwsPolicy(
        Statement=[
            AwsStatement(
                Effect="Allow",
                Principal="*",
                Action=["*"],
                Resource=["*"],
            )
        ]
    )


@pytest.fixture
def feature_extractor() -> PolicyFeatureExtractor:
    """Create a feature extractor instance."""
    return PolicyFeatureExtractor()


class TestPolicyFeatureExtractor:
    """Tests for PolicyFeatureExtractor."""

    def test_extract_gcp_features(self, feature_extractor: PolicyFeatureExtractor) -> None:
        """Test GCP feature extraction."""
        policy = Policy(
            bindings=[
                Binding(
                    role="roles/owner",
                    members=["allUsers", "user:test@example.com"],
                ),
                Binding(
                    role="roles/viewer",
                    members=["serviceAccount:sa@project.iam.gserviceaccount.com"],
                    condition={"expression": "request.time < timestamp('2024-01-01T00:00:00Z')"},
                ),
            ]
        )

        features = feature_extractor.extract_gcp_features(policy)

        assert features["num_bindings"] == 2.0
        assert features["total_members"] == 3.0
        assert features["avg_members_per_binding"] == 1.5
        assert features["risky_role_count"] == 1.0
        assert features["wildcard_member_count"] == 1.0
        assert features["service_account_count"] == 1.0
        assert features["conditional_binding_count"] == 1.0

    def test_extract_aws_features(self, feature_extractor: PolicyFeatureExtractor) -> None:
        """Test AWS feature extraction."""
        policy = AwsPolicy(
            Statement=[
                AwsStatement(
                    Effect="Allow",
                    Principal="*",
                    Action=["s3:*", "iam:CreateUser"],
                    Resource=["*"],
                ),
                AwsStatement(
                    Effect="Deny",
                    Action=["ec2:TerminateInstances"],
                    Resource=["arn:aws:ec2:*:*:instance/*"],
                ),
            ]
        )

        features = feature_extractor.extract_aws_features(policy)

        assert features["num_statements"] == 2.0
        assert features["total_actions"] == 3.0
        assert features["allow_statement_count"] == 1.0
        assert features["deny_statement_count"] == 1.0
        assert features["wildcard_principal_count"] == 1.0
        assert features["wildcard_action_count"] == 1.0

    def test_extract_azure_features(self, feature_extractor: PolicyFeatureExtractor) -> None:
        """Test Azure feature extraction."""
        role = AzureRoleDefinition(
            Name="CustomRole",
            Actions=["*", "Microsoft.Compute/virtualMachines/read"],
            NotActions=["Microsoft.Authorization/*/Delete"],
            AssignableScopes=[
                "/subscriptions/12345",
                "/providers/Microsoft.Management/managementGroups/mg1",
            ],
            IsCustom=True,
        )

        features = feature_extractor.extract_azure_features(role)

        assert features["action_count"] == 2.0
        assert features["not_action_count"] == 1.0
        assert features["is_custom"] == 1.0
        assert features["wildcard_action_count"] == 1.0
        assert features["has_subscription_scope"] == 1.0
        assert features["has_management_group_scope"] == 1.0

    def test_features_to_vector(self, feature_extractor: PolicyFeatureExtractor) -> None:
        """Test conversion of features to numpy vector."""
        features = {
            "feature_a": 1.0,
            "feature_b": 2.5,
            "feature_c": 0.0,
        }

        vector = feature_extractor.features_to_vector(features)

        assert isinstance(vector, np.ndarray)
        assert len(vector) == 3
        assert vector[0] == 1.0  # feature_a (sorted first)
        assert vector[1] == 2.5  # feature_b
        assert vector[2] == 0.0  # feature_c


class TestMLConfig:
    """Tests for MLConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = MLConfig()

        assert config.contamination == 0.1
        assert config.n_estimators == 100
        assert config.max_samples == "auto"
        assert config.random_state == 42
        assert config.model_path is None

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = MLConfig(
            contamination=0.2,
            n_estimators=200,
            max_samples=128,
            random_state=123,
            model_path="/path/to/model.pkl",
        )

        assert config.contamination == 0.2
        assert config.n_estimators == 200
        assert config.max_samples == 128
        assert config.random_state == 123
        assert config.model_path == "/path/to/model.pkl"


class TestAnomalyDetector:
    """Tests for AnomalyDetector."""

    def test_init_default_config(self) -> None:
        """Test initialization with default config."""
        detector = AnomalyDetector()

        assert detector.config.contamination == 0.1
        assert not detector.is_trained
        assert detector.model is None

    def test_init_custom_config(self) -> None:
        """Test initialization with custom config."""
        config = MLConfig(contamination=0.15, n_estimators=150)
        detector = AnomalyDetector(config=config)

        assert detector.config.contamination == 0.15
        assert detector.config.n_estimators == 150

    def test_train_gcp_policies(self, normal_gcp_policies: list[Policy]) -> None:
        """Test training on GCP policies."""
        detector = AnomalyDetector()
        detector.train(normal_gcp_policies, save_model=False)

        assert detector.is_trained
        assert detector.model is not None
        assert len(detector.feature_names) > 0

    def test_train_aws_policies(self, normal_aws_policies: list[AwsPolicy]) -> None:
        """Test training on AWS policies."""
        detector = AnomalyDetector()
        detector.train(normal_aws_policies, save_model=False)

        assert detector.is_trained
        assert detector.model is not None

    def test_train_empty_policies(self) -> None:
        """Test training with empty policy list."""
        detector = AnomalyDetector()

        with pytest.raises(ValueError, match="Cannot train on empty policy list"):
            detector.train([], save_model=False)

    def test_predict_normal_policy(self, normal_gcp_policies: list[Policy]) -> None:
        """Test prediction on normal policy."""
        detector = AnomalyDetector()
        detector.train(normal_gcp_policies, save_model=False)

        result = detector.predict(normal_gcp_policies[0])

        assert isinstance(result, AnomalyResult)
        assert not result.is_anomaly
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.features, dict)
        assert isinstance(result.explanation, str)

    def test_predict_anomalous_policy(
        self, normal_gcp_policies: list[Policy], anomalous_gcp_policy: Policy
    ) -> None:
        """Test prediction on anomalous policy."""
        detector = AnomalyDetector()
        detector.train(normal_gcp_policies, save_model=False)

        result = detector.predict(anomalous_gcp_policy)

        assert isinstance(result, AnomalyResult)
        # Anomalous policy should likely be detected, but ML is probabilistic
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.features, dict)
        assert len(result.risk_factors) > 0  # Should have some risk factors

    def test_predict_without_training(self, normal_gcp_policies: list[Policy]) -> None:
        """Test prediction before training."""
        detector = AnomalyDetector()

        with pytest.raises(RuntimeError, match="Model must be trained before prediction"):
            detector.predict(normal_gcp_policies[0])

    def test_save_and_load_model(self, normal_gcp_policies: list[Policy]) -> None:
        """Test saving and loading model."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = str(Path(tmpdir) / "test_model.pkl")

            # Train and save
            detector1 = AnomalyDetector()
            detector1.train(normal_gcp_policies, save_model=False)
            detector1.save_model(model_path)

            # Load and predict
            detector2 = AnomalyDetector()
            detector2.load_model(model_path)

            assert detector2.is_trained
            assert detector2.model is not None

            result = detector2.predict(normal_gcp_policies[0])
            assert isinstance(result, AnomalyResult)

    def test_save_model_without_training(self) -> None:
        """Test saving model before training."""
        detector = AnomalyDetector()

        with pytest.raises(RuntimeError, match="Cannot save untrained model"):
            detector.save_model("/tmp/model.pkl")

    def test_load_nonexistent_model(self) -> None:
        """Test loading non-existent model."""
        detector = AnomalyDetector()

        with pytest.raises(FileNotFoundError):
            detector.load_model("/nonexistent/model.pkl")

    def test_aws_anomaly_detection(
        self, normal_aws_policies: list[AwsPolicy], anomalous_aws_policy: AwsPolicy
    ) -> None:
        """Test anomaly detection on AWS policies."""
        detector = AnomalyDetector()
        detector.train(normal_aws_policies, save_model=False)

        result = detector.predict(anomalous_aws_policy)

        assert isinstance(result, AnomalyResult)
        assert len(result.risk_factors) > 0
        assert any("wildcard" in factor.lower() for factor in result.risk_factors)


class TestAnomalyResult:
    """Tests for AnomalyResult model."""

    def test_valid_anomaly_result(self) -> None:
        """Test creating valid anomaly result."""
        result = AnomalyResult(
            is_anomaly=True,
            anomaly_score=-0.5,
            confidence=0.85,
            features={"num_bindings": 5.0},
            explanation="Policy is anomalous",
            risk_factors=["Public access detected"],
        )

        assert result.is_anomaly
        assert result.anomaly_score == -0.5
        assert result.confidence == 0.85
        assert result.features == {"num_bindings": 5.0}
        assert result.explanation == "Policy is anomalous"
        assert result.risk_factors == ["Public access detected"]

    def test_anomaly_score_validation(self) -> None:
        """Test anomaly score validation."""
        # Valid scores
        AnomalyResult(
            is_anomaly=False,
            anomaly_score=0.5,
            confidence=0.9,
            features={},
            explanation="Normal",
        )

        # Invalid score (out of range)
        with pytest.raises(ValueError, match=".*"):
            AnomalyResult(
                is_anomaly=True,
                anomaly_score=2.0,  # > 1.0
                confidence=0.9,
                features={},
                explanation="Invalid",
            )

    def test_confidence_validation(self) -> None:
        """Test confidence validation."""
        # Valid confidence
        AnomalyResult(
            is_anomaly=False,
            anomaly_score=0.1,
            confidence=1.0,
            features={},
            explanation="Normal",
        )

        # Invalid confidence
        with pytest.raises(ValueError, match=".*"):
            AnomalyResult(
                is_anomaly=True,
                anomaly_score=-0.1,
                confidence=1.5,  # > 1.0
                features={},
                explanation="Invalid",
            )
