"""Tests for IaC integration."""

import json
import tempfile
from pathlib import Path

import pytest

from src.core.config import AppConfig
from src.core.models import AwsPolicy, AwsStatement, Binding, Policy
from src.iac.scanner import IacScanner
from src.iac.terraform import TerraformParser


@pytest.fixture
def mock_terraform_plan():
    return {
        "resource_changes": [
            {
                "type": "google_project_iam_binding",
                "change": {
                    "actions": ["create"],
                    "after": {"role": "roles/owner", "members": ["allUsers"]},
                },
            },
            {
                "type": "aws_iam_policy",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "policy": json.dumps(
                            {
                                "Version": "2012-10-17",
                                "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}],
                            }
                        )
                    },
                },
            },
            {
                "type": "google_compute_instance",  # Ignored
                "change": {"actions": ["create"], "after": {}},
            },
        ]
    }


class TestTerraformParser:
    def test_parse_plan(self, mock_terraform_plan):
        parser = TerraformParser()

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            json.dump(mock_terraform_plan, f)
            path = f.name

        try:
            resources = parser.parse_plan(path)

            assert len(resources["gcp"]) == 1
            assert len(resources["aws"]) == 1
            # Check parsed GCP content
            assert resources["gcp"][0].bindings[0].role == "roles/owner"
            # Check parsed AWS content
            assert resources["aws"][0].Statement[0].Effect == "Allow"
            # It comes out as a string because it's a string in the JSON
            assert resources["aws"][0].Statement[0].Action == "*"

        finally:
            Path(path).unlink()


class TestIacScanner:
    def test_scan(self):
        config = AppConfig(risky_roles=["roles/owner"], wildcard_members=["allUsers"])
        scanner = IacScanner(config)

        # Manually construct parsed resources similar to what parser returns
        resources = {
            "gcp": [Policy(bindings=[Binding(role="roles/owner", members=["allUsers"])])],
            "aws": [AwsPolicy(Statement=[AwsStatement(Effect="Allow", Action="*", Resource="*")])],
            "azure": [],
        }

        findings = scanner.scan(resources)

        # Expecting at least:
        # 1. RISKY_ROLE (GCP)
        # 2. WILDCARD_ACCESS (GCP)
        # 3. AWS_UNRESTRICTED_ADMIN (AWS)
        assert len(findings) >= 3

        ids = [f.id for f in findings]
        assert "RISKY_ROLE" in ids
        assert "WILDCARD_ACCESS" in ids
        assert "AWS_UNRESTRICTED_ADMIN" in ids

        assert any("terraform" in f.resource for f in findings)
