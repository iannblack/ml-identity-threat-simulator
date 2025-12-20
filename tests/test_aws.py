import json
import os
import tempfile

import pytest

from src.core.config import AppConfig
from src.core.models import AwsPolicy
from src.iam.aws_auditor import AwsAuditor
from src.iam.aws_parsers import load_aws_policy_from_json


class TestAwsParser:
    def test_load_valid_policy(self):
        policy_data = {
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Action": "s3:ListBucket", "Resource": "arn:aws:s3:::example"}
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy_data, f)
            temp_path = f.name

        try:
            policy = load_aws_policy_from_json(temp_path)
            assert isinstance(policy, AwsPolicy)
            assert len(policy.Statement) == 1
            assert policy.Statement[0].Action == "s3:ListBucket"
        finally:
            os.unlink(temp_path)

    def test_normalize_single_statement_dict(self):
        """Test that a single dict Statement (not list) is normalized to a list."""
        policy_data = {
            "Version": "2012-10-17",
            "Statement": {"Effect": "Deny", "Action": "*", "Resource": "*"},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy_data, f)
            temp_path = f.name

        try:
            policy = load_aws_policy_from_json(temp_path)
            assert isinstance(policy.Statement, list)
            assert len(policy.Statement) == 1
            assert policy.Statement[0].Effect == "Deny"
        finally:
            os.unlink(temp_path)


class TestAwsAuditor:
    @pytest.fixture
    def auditor(self):
        config = AppConfig(risky_roles=[], wildcard_members=[])
        return AwsAuditor(config=config)

    def test_detect_admin_access(self, auditor):
        policy = AwsPolicy(Statement=[{"Effect": "Allow", "Action": "*", "Resource": "*"}])
        findings = auditor.audit_policy(policy)
        assert len(findings) == 1
        assert findings[0].id == "AWS_UNRESTRICTED_ADMIN"

    def test_detect_admin_access_list(self, auditor):
        policy = AwsPolicy(Statement=[{"Effect": "Allow", "Action": ["*"], "Resource": ["*"]}])
        findings = auditor.audit_policy(policy)
        assert len(findings) == 1
        assert findings[0].id == "AWS_UNRESTRICTED_ADMIN"

    def test_detect_public_access_principal_star(self, auditor):
        policy = AwsPolicy(
            Statement=[
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": "arn:aws:s3:::bucket/*",
                }
            ]
        )
        findings = auditor.audit_policy(policy)
        assert len(findings) == 1
        assert findings[0].id == "AWS_PUBLIC_ACCESS"

    def test_detect_public_access_aws_star(self, auditor):
        policy = AwsPolicy(
            Statement=[
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": "s3:GetObject",
                    "Resource": "arn:aws:s3:::bucket/*",
                }
            ]
        )
        findings = auditor.audit_policy(policy)
        assert len(findings) == 1
        assert findings[0].id == "AWS_PUBLIC_ACCESS"

    def test_safe_policy_no_findings(self, auditor):
        policy = AwsPolicy(
            Statement=[
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "arn:aws:iam::123:user/alice"},
                    "Action": ["s3:ListBucket"],
                    "Resource": ["arn:aws:s3:::my-bucket"],
                }
            ]
        )
        findings = auditor.audit_policy(policy)
        assert len(findings) == 0

    def test_deny_statements_ignored(self, auditor):
        """Ensure Deny statements don't trigger findings."""
        policy = AwsPolicy(Statement=[{"Effect": "Deny", "Action": "*", "Resource": "*"}])
        findings = auditor.audit_policy(policy)
        assert len(findings) == 0
