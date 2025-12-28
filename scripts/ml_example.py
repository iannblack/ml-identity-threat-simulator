#!/usr/bin/env python3
"""Example script demonstrating ML-based anomaly detection."""

import json
import logging
from pathlib import Path

from src.core.models import Binding, Policy
from src.ml.detector import AnomalyDetector
from src.ml.models import MLConfig

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def create_sample_policies() -> tuple[list[Policy], Policy, Policy]:
    """
    Create sample policies for demonstration.

    Returns:
        Tuple of (normal_policies, normal_test_policy, anomalous_policy)
    """
    # Create 15 normal training policies
    normal_policies = []
    for i in range(15):
        policy = Policy(
            bindings=[
                Binding(
                    role="roles/viewer",
                    members=[
                        f"user:employee{i}@company.com",
                        "serviceAccount:app@project.iam.gserviceaccount.com",
                    ],
                ),
                Binding(
                    role="roles/editor",
                    members=[f"user:developer{i}@company.com"],
                ),
                Binding(
                    role="roles/logging.viewer",
                    members=[f"group:team{i}@company.com"],
                ),
            ]
        )
        normal_policies.append(policy)

    # Create a normal test policy (should be classified as normal)
    normal_test_policy = Policy(
        bindings=[
            Binding(
                role="roles/viewer",
                members=["user:john.doe@company.com"],
            ),
            Binding(
                role="roles/editor",
                members=["user:jane.smith@company.com"],
            ),
        ]
    )

    # Create an anomalous policy (should be detected as anomaly)
    anomalous_policy = Policy(
        bindings=[
            Binding(
                role="roles/owner",  # Risky role
                members=["allUsers", "allAuthenticatedUsers"],  # Public access
            ),
            Binding(
                role="roles/iam.securityAdmin",  # Risky role
                members=["user:suspicious@external-domain.com"],
            ),
            Binding(
                role="roles/storage.admin",  # Risky role
                members=["serviceAccount:unknown@attacker.iam.gserviceaccount.com"],
            ),
        ]
    )

    return normal_policies, normal_test_policy, anomalous_policy


def main() -> None:
    """Run the ML anomaly detection example."""
    logger.info("=" * 60)
    logger.info("ML-based Anomaly Detection Example")
    logger.info("=" * 60)

    # Step 1: Create sample data
    logger.info("\n[1] Creating sample policies...")
    normal_policies, normal_test, anomalous = create_sample_policies()
    logger.info(f"    ✓ Created {len(normal_policies)} normal training policies")
    logger.info(f"    ✓ Created 1 normal test policy")
    logger.info(f"    ✓ Created 1 anomalous policy")

    # Step 2: Configure and initialize detector
    logger.info("\n[2] Initializing ML detector...")
    config = MLConfig(
        contamination=0.1,  # Expect 10% anomalies
        n_estimators=100,
        random_state=42,
        model_path="models/demo_detector.pkl",
    )
    detector = AnomalyDetector(config=config)
    logger.info(f"    ✓ Contamination: {config.contamination}")
    logger.info(f"    ✓ Estimators: {config.n_estimators}")

    # Step 3: Train the model
    logger.info("\n[3] Training model on normal policies...")
    detector.train(normal_policies, save_model=True)
    logger.info(f"    ✓ Training completed")
    logger.info(f"    ✓ Model saved to: {config.model_path}")

    # Step 4: Test on normal policy
    logger.info("\n[4] Testing on NORMAL policy...")
    normal_result = detector.predict(normal_test)
    logger.info(f"    Anomaly Detected: {normal_result.is_anomaly}")
    logger.info(f"    Confidence: {normal_result.confidence:.1%}")
    logger.info(f"    Anomaly Score: {normal_result.anomaly_score:.3f}")
    logger.info(f"    Explanation: {normal_result.explanation}")

    # Step 5: Test on anomalous policy
    logger.info("\n[5] Testing on ANOMALOUS policy...")
    anomaly_result = detector.predict(anomalous)
    logger.info(f"    Anomaly Detected: {anomaly_result.is_anomaly}")
    logger.info(f"    Confidence: {anomaly_result.confidence:.1%}")
    logger.info(f"    Anomaly Score: {anomaly_result.anomaly_score:.3f}")
    logger.info(f"    Explanation: {anomaly_result.explanation}")
    if anomaly_result.risk_factors:
        logger.info(f"    Risk Factors:")
        for factor in anomaly_result.risk_factors:
            logger.info(f"      • {factor}")

    # Step 6: Save results
    logger.info("\n[6] Saving results...")
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    # Save normal result
    with open(results_dir / "normal_result.json", "w") as f:
        json.dump(normal_result.model_dump(), f, indent=2)

    # Save anomaly result
    with open(results_dir / "anomaly_result.json", "w") as f:
        json.dump(anomaly_result.model_dump(), f, indent=2)

    logger.info(f"    ✓ Results saved to {results_dir}/")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Summary:")
    logger.info("=" * 60)
    logger.info(f"Normal Policy:    {'✓ PASS' if not normal_result.is_anomaly else '✗ FAIL'}")
    logger.info(f"Anomalous Policy: {'✓ DETECTED' if anomaly_result.is_anomaly else '✗ MISSED'}")
    logger.info("=" * 60)

    # Demonstrate model reload
    logger.info("\n[7] Demonstrating model persistence...")
    new_detector = AnomalyDetector()
    new_detector.load_model(config.model_path)
    logger.info(f"    ✓ Model reloaded from: {config.model_path}")

    # Verify it produces same results
    reloaded_result = new_detector.predict(anomalous)
    assert reloaded_result.is_anomaly == anomaly_result.is_anomaly
    logger.info(f"    ✓ Predictions match: {reloaded_result.is_anomaly}")

    logger.info("\n✅ Example completed successfully!\n")


if __name__ == "__main__":
    main()
