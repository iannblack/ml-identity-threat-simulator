"""ML-specific models for anomaly detection."""

from typing import Any

from pydantic import BaseModel, Field


class MLConfig(BaseModel):
    """Configuration for ML-based anomaly detection."""

    contamination: float = Field(
        default=0.1,
        ge=0.0,
        le=0.5,
        description="Expected proportion of anomalies in the dataset",
    )
    n_estimators: int = Field(
        default=100, ge=10, le=500, description="Number of base estimators in ensemble"
    )
    max_samples: int | str = Field(
        default="auto", description="Number of samples to draw from X to train each estimator"
    )
    random_state: int = Field(default=42, description="Random state for reproducibility")
    model_path: str | None = Field(default=None, description="Path to save/load trained model")


class AnomalyResult(BaseModel):
    """Result of anomaly detection on a policy."""

    is_anomaly: bool = Field(..., description="Whether the policy is anomalous")
    anomaly_score: float = Field(
        ..., ge=-1.0, le=1.0, description="Anomaly score (negative means anomaly)"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence of the prediction (0-1)")
    features: dict[str, Any] = Field(
        default_factory=dict, description="Extracted features used for detection"
    )
    explanation: str = Field(..., description="Human-readable explanation of the result")
    risk_factors: list[str] = Field(
        default_factory=list, description="List of contributing risk factors"
    )
