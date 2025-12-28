"""Anomaly detector for IAM policies using Isolation Forest."""

import logging
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from src.core.models import AwsPolicy, AzureRoleDefinition, Policy

from .feature_extractor import PolicyFeatureExtractor
from .models import AnomalyResult, MLConfig

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """ML-based anomaly detector for IAM policies."""

    def __init__(self, config: MLConfig | None = None) -> None:
        """
        Initialize the anomaly detector.

        Args:
            config: ML configuration. If None, uses default configuration.
        """
        self.config = config or MLConfig()
        self.feature_extractor = PolicyFeatureExtractor()
        self.model: IsolationForest | None = None
        self.is_trained = False
        self.feature_names: list[str] = []

    def train(
        self, policies: list[Policy | AwsPolicy | AzureRoleDefinition], save_model: bool = True
    ) -> None:
        """
        Train the anomaly detection model on a set of policies.

        Args:
            policies: List of policies to train on (expected to be mostly normal).
            save_model: Whether to save the trained model to disk.

        Raises:
            ValueError: If policies list is empty or contains unsupported types.
        """
        if not policies:
            msg = "Cannot train on empty policy list"
            raise ValueError(msg)

        logger.info(f"Training anomaly detector on {len(policies)} policies")

        # Extract features from all policies
        feature_vectors = []
        for policy in policies:
            features = self.feature_extractor.extract_features(policy)
            vector = self.feature_extractor.features_to_vector(features)
            feature_vectors.append(vector)

        x = np.array(feature_vectors)

        # Get feature names from first policy
        first_features = self.feature_extractor.extract_features(policies[0])
        self.feature_names = sorted(first_features.keys())

        # Initialize and train Isolation Forest
        max_samples = self.config.max_samples
        if isinstance(max_samples, str) and max_samples == "auto":
            max_samples = min(256, len(policies))

        self.model = IsolationForest(
            contamination=self.config.contamination,
            n_estimators=self.config.n_estimators,
            max_samples=max_samples,
            random_state=self.config.random_state,
            n_jobs=-1,  # Use all available cores
        )

        self.model.fit(x)
        self.is_trained = True

        logger.info("Model training completed successfully")

        # Save model if requested
        if save_model and self.config.model_path:
            self.save_model(self.config.model_path)

    def predict(self, policy: Policy | AwsPolicy | AzureRoleDefinition) -> AnomalyResult:
        """
        Predict whether a policy is anomalous.

        Args:
            policy: IAM policy to analyze.

        Returns:
            AnomalyResult containing prediction and explanation.

        Raises:
            RuntimeError: If model hasn't been trained yet.
        """
        if not self.is_trained or self.model is None:
            msg = "Model must be trained before prediction. Call train() first."
            raise RuntimeError(msg)

        # Extract features
        features = self.feature_extractor.extract_features(policy)
        x = self.feature_extractor.features_to_vector(features).reshape(1, -1)

        # Predict (-1 for anomaly, 1 for normal)
        prediction = self.model.predict(x)[0]
        is_anomaly = prediction == -1

        # Get anomaly score (negative means more anomalous)
        anomaly_score = float(self.model.score_samples(x)[0])

        # Convert score to confidence (0-1 range)
        # Scores typically range from -0.5 to 0.5, normalize to 0-1
        confidence = float(1.0 / (1.0 + np.exp(-anomaly_score * 10)))

        # Generate explanation and risk factors
        explanation, risk_factors = self._generate_explanation(
            features, is_anomaly, anomaly_score, policy
        )

        return AnomalyResult(
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            confidence=confidence,
            features=features,
            explanation=explanation,
            risk_factors=risk_factors,
        )

    def _get_gcp_risk_factors(self, features: dict[str, float]) -> list[str]:
        """Extract risk factors for GCP policies."""
        risk_factors = []
        if features.get("wildcard_member_count", 0) > 0:
            risk_factors.append(
                f"Public access detected: {int(features['wildcard_member_count'])} wildcard members"
            )
        if features.get("risky_role_ratio", 0) > 0.3:
            risk_factors.append(
                f"High proportion of risky roles: {features['risky_role_ratio']:.1%}"
            )
        if features.get("service_account_ratio", 0) > 0.8:
            risk_factors.append("Very high service account usage")
        if (
            features.get("conditional_binding_ratio", 0) < 0.1
            and features.get("num_bindings", 0) > 5
        ):
            risk_factors.append("Low usage of conditional bindings for large policy")
        return risk_factors

    def _get_aws_risk_factors(self, features: dict[str, float]) -> list[str]:
        """Extract risk factors for AWS policies."""
        risk_factors = []
        if features.get("wildcard_principal_count", 0) > 0:
            risk_factors.append(
                f"Wildcard principals detected: {int(features['wildcard_principal_count'])} statements"
            )
        if features.get("wildcard_action_count", 0) > 0:
            risk_factors.append(
                f"Wildcard actions detected: {int(features['wildcard_action_count'])} actions"
            )
        if features.get("risky_action_count", 0) > 0:
            risk_factors.append(f"Risky actions: {int(features['risky_action_count'])} statements")
        if features.get("allow_ratio", 0) == 1.0 and features.get("num_statements", 0) > 5:
            risk_factors.append("No explicit deny statements")
        return risk_factors

    def _get_azure_risk_factors(self, features: dict[str, float]) -> list[str]:
        """Extract risk factors for Azure policies."""
        risk_factors = []
        if features.get("wildcard_action_count", 0) > 0:
            risk_factors.append(
                f"Wildcard actions detected: {int(features['wildcard_action_count'])} actions"
            )
        if features.get("risky_action_ratio", 0) > 0.3:
            risk_factors.append(
                f"High proportion of risky actions: {features['risky_action_ratio']:.1%}"
            )
        if features.get("has_management_group_scope", 0) == 1.0:
            risk_factors.append("Management group scope assigned")
        return risk_factors

    def _generate_explanation(
        self,
        features: dict[str, float],
        is_anomaly: bool,
        score: float,
        policy: Policy | AwsPolicy | AzureRoleDefinition,
    ) -> tuple[str, list[str]]:
        """Generate human-readable explanation for the prediction."""
        # Analyze features to identify risk factors
        if isinstance(policy, Policy):
            risk_factors = self._get_gcp_risk_factors(features)
        elif isinstance(policy, AwsPolicy):
            risk_factors = self._get_aws_risk_factors(features)
        else:  # AzureRoleDefinition
            risk_factors = self._get_azure_risk_factors(features)

        # Generate overall explanation
        if is_anomaly:
            severity = "highly" if score < -0.3 else "moderately"
            explanation = (
                f"This policy is {severity} anomalous (score: {score:.3f}). "
                f"It deviates significantly from normal patterns. "
            )
            if risk_factors:
                explanation += f"Risk factors: {'; '.join(risk_factors[:3])}"
            else:
                explanation += "The policy structure is unusual compared to the training data."
        else:
            explanation = (
                f"This policy appears normal (score: {score:.3f}). "
                f"It follows typical patterns observed in the training data."
            )
            if risk_factors:
                explanation += f" However, note: {'; '.join(risk_factors[:2])}"

        return explanation, risk_factors

    def save_model(self, path: str) -> None:
        """
        Save the trained model to disk.

        Args:
            path: Path to save the model file.

        Raises:
            RuntimeError: If model hasn't been trained yet.
        """
        if not self.is_trained or self.model is None:
            msg = "Cannot save untrained model"
            raise RuntimeError(msg)

        model_path = Path(path)
        model_path.parent.mkdir(parents=True, exist_ok=True)

        # Save model and related data
        model_data = {
            "model": self.model,
            "config": self.config.model_dump(),
            "feature_names": self.feature_names,
        }

        joblib.dump(model_data, model_path)
        logger.info(f"Model saved to {model_path}")

    def load_model(self, path: str) -> None:
        """
        Load a trained model from disk.

        Args:
            path: Path to the model file.

        Raises:
            FileNotFoundError: If model file doesn't exist.
        """
        model_path = Path(path)
        if not model_path.exists():
            msg = f"Model file not found: {model_path}"
            raise FileNotFoundError(msg)

        # Load model and related data
        model_data = joblib.load(model_path)

        self.model = model_data["model"]
        self.feature_names = model_data["feature_names"]
        self.config = MLConfig(**model_data["config"])
        self.is_trained = True

        logger.info(f"Model loaded from {model_path}")

    def get_feature_importance(self) -> dict[str, float]:
        """
        Get feature importance scores (approximation for Isolation Forest).

        Returns:
            Dictionary mapping feature names to importance scores.

        Raises:
            RuntimeError: If model hasn't been trained yet.
        """
        if not self.is_trained or self.model is None:
            msg = "Model must be trained first"
            raise RuntimeError(msg)

        # For Isolation Forest, we can't get traditional feature importance
        # Instead, return average feature values as a proxy
        logger.warning(
            "Isolation Forest doesn't provide feature importance. Returning placeholder values."
        )

        return {name: 1.0 / len(self.feature_names) for name in self.feature_names}
