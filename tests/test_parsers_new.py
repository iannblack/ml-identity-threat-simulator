"""
Comprehensive tests for iam.parsers module.
Tests policy loading from JSON files with various formats and edge cases.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.iam.parsers import load_policy_from_json


class TestLoadPolicyFromJson:
    """Tests for load_policy_from_json function."""

    def test_load_simple_policy(self):
        """Test loading a simple valid policy."""
        policy_data = {
            "bindings": [{"role": "roles/viewer", "members": ["user:viewer@example.com"]}]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy_data, f)
            temp_path = f.name

        try:
            policy = load_policy_from_json(temp_path)
            assert len(policy.bindings) == 1
            assert policy.bindings[0].role == "roles/viewer"
            assert policy.bindings[0].members == ["user:viewer@example.com"]
        finally:
            os.unlink(temp_path)

    def test_load_policy_with_multiple_bindings(self):
        """Test loading policy with multiple bindings."""
        policy_data = {
            "bindings": [
                {"role": "roles/owner", "members": ["user:owner@example.com"]},
                {"role": "roles/editor", "members": ["user:editor@example.com"]},
                {"role": "roles/viewer", "members": ["user:viewer@example.com"]},
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy_data, f)
            temp_path = f.name

        try:
            policy = load_policy_from_json(temp_path)
            assert len(policy.bindings) == 3
            roles = [b.role for b in policy.bindings]
            assert "roles/owner" in roles
            assert "roles/editor" in roles
            assert "roles/viewer" in roles
        finally:
            os.unlink(temp_path)

    def test_load_policy_with_etag_and_version(self):
        """Test loading policy with etag and version."""
        policy_data = {
            "bindings": [{"role": "roles/viewer", "members": ["user:test@example.com"]}],
            "etag": "BwXhFM7aN_k=",
            "version": 3,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy_data, f)
            temp_path = f.name

        try:
            policy = load_policy_from_json(temp_path)
            assert policy.etag == "BwXhFM7aN_k="
            assert policy.version == 3
        finally:
            os.unlink(temp_path)

    def test_load_policy_with_condition(self):
        """Test loading policy with IAM conditions."""
        policy_data = {
            "bindings": [
                {
                    "role": "roles/storage.admin",
                    "members": ["user:admin@example.com"],
                    "condition": {
                        "title": "Expires in 2024",
                        "expression": "request.time < timestamp('2024-12-31T23:59:59Z')",
                    },
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy_data, f)
            temp_path = f.name

        try:
            policy = load_policy_from_json(temp_path)
            assert policy.bindings[0].condition is not None
            assert "expression" in policy.bindings[0].condition
        finally:
            os.unlink(temp_path)

    def test_load_policy_with_multiple_members(self):
        """Test loading binding with multiple members."""
        policy_data = {
            "bindings": [
                {
                    "role": "roles/viewer",
                    "members": [
                        "user:user1@example.com",
                        "user:user2@example.com",
                        "serviceAccount:sa@project.iam.gserviceaccount.com",
                        "group:admins@example.com",
                    ],
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy_data, f)
            temp_path = f.name

        try:
            policy = load_policy_from_json(temp_path)
            assert len(policy.bindings[0].members) == 4
            assert "serviceAccount:sa@project.iam.gserviceaccount.com" in policy.bindings[0].members
        finally:
            os.unlink(temp_path)

    def test_load_policy_empty_bindings(self):
        """Test loading policy with empty bindings list."""
        policy_data = {"bindings": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy_data, f)
            temp_path = f.name

        try:
            policy = load_policy_from_json(temp_path)
            assert len(policy.bindings) == 0
        finally:
            os.unlink(temp_path)

    def test_load_policy_missing_bindings_key(self):
        """Test loading policy without bindings key."""
        policy_data = {"etag": "test", "version": 1}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy_data, f)
            temp_path = f.name

        try:
            policy = load_policy_from_json(temp_path)
            # Should create policy with empty bindings
            assert len(policy.bindings) == 0
        finally:
            os.unlink(temp_path)

    def test_load_policy_default_version(self):
        """Test that missing version defaults to 1."""
        policy_data = {"bindings": [{"role": "roles/viewer", "members": ["user:test@example.com"]}]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy_data, f)
            temp_path = f.name

        try:
            policy = load_policy_from_json(temp_path)
            assert policy.version == 1
        finally:
            os.unlink(temp_path)


class TestLoadPolicyErrors:
    """Tests for error handling in load_policy_from_json."""

    def test_load_nonexistent_file(self):
        """Test loading from non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_policy_from_json("nonexistent_file.json")

    def test_load_invalid_json(self):
        """Test loading invalid JSON raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                load_policy_from_json(temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_empty_file(self):
        """Test loading empty file raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                load_policy_from_json(temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_binding_missing_role(self):
        """Test loading binding without role raises error."""
        policy_data = {"bindings": [{"members": ["user:test@example.com"]}]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy_data, f)
            temp_path = f.name

        try:
            with pytest.raises(KeyError):
                load_policy_from_json(temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_binding_missing_members(self):
        """Test loading binding without members (should use empty list)."""
        policy_data = {"bindings": [{"role": "roles/viewer"}]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy_data, f)
            temp_path = f.name

        try:
            policy = load_policy_from_json(temp_path)
            # Should default to empty members list
            assert policy.bindings[0].members == []
        finally:
            os.unlink(temp_path)


class TestRealWorldPolicies:
    """Tests with realistic GCP policy structures."""

    def test_load_gcp_project_policy(self):
        """Test loading a realistic GCP project policy."""
        policy_data = {
            "bindings": [
                {"role": "roles/owner", "members": ["user:admin@example.com"]},
                {
                    "role": "roles/editor",
                    "members": [
                        "serviceAccount:12345-compute@developer.gserviceaccount.com",
                        "user:developer@example.com",
                    ],
                },
                {
                    "role": "roles/viewer",
                    "members": ["group:viewers@example.com", "user:analyst@example.com"],
                },
                {
                    "role": "roles/bigquery.admin",
                    "members": ["serviceAccount:bq-admin@project.iam.gserviceaccount.com"],
                },
                {"role": "roles/storage.objectViewer", "members": ["allAuthenticatedUsers"]},
            ],
            "etag": "BwXhFM7aN_k=",
            "version": 1,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy_data, f)
            temp_path = f.name

        try:
            policy = load_policy_from_json(temp_path)
            assert len(policy.bindings) == 5
            assert policy.etag == "BwXhFM7aN_k="

            # Verify specific bindings
            owner_binding = [b for b in policy.bindings if b.role == "roles/owner"][0]
            assert "user:admin@example.com" in owner_binding.members

            storage_binding = [
                b for b in policy.bindings if b.role == "roles/storage.objectViewer"
            ][0]
            assert "allAuthenticatedUsers" in storage_binding.members
        finally:
            os.unlink(temp_path)

    def test_load_policy_with_complex_conditions(self):
        """Test loading policy with complex IAM conditions."""
        policy_data = {
            "bindings": [
                {
                    "role": "roles/storage.admin",
                    "members": ["user:admin@example.com"],
                    "condition": {
                        "title": "Limited time access",
                        "description": "Expires at end of 2024",
                        "expression": "request.time < timestamp('2024-12-31T23:59:59Z')",
                    },
                },
                {
                    "role": "roles/compute.admin",
                    "members": ["user:ops@example.com"],
                    "condition": {
                        "title": "Resource specific",
                        "expression": "resource.name.startsWith('projects/my-project/zones/us-central1')",
                    },
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy_data, f)
            temp_path = f.name

        try:
            policy = load_policy_from_json(temp_path)
            assert len(policy.bindings) == 2

            for binding in policy.bindings:
                assert binding.condition is not None
                assert "expression" in binding.condition
        finally:
            os.unlink(temp_path)


class TestEdgeCases:
    """Tests for edge cases and unusual inputs."""

    def test_load_policy_with_extra_fields(self):
        """Test that extra fields in JSON are ignored."""
        policy_data = {
            "bindings": [
                {
                    "role": "roles/viewer",
                    "members": ["user:test@example.com"],
                    "extra_field": "should be ignored",
                }
            ],
            "unknown_field": "also ignored",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy_data, f)
            temp_path = f.name

        try:
            policy = load_policy_from_json(temp_path)
            # Should load successfully, ignoring extra fields
            assert len(policy.bindings) == 1
        finally:
            os.unlink(temp_path)

    def test_load_policy_with_unicode(self):
        """Test loading policy with unicode characters."""
        policy_data = {"bindings": [{"role": "roles/viewer", "members": ["user:tëst@éxample.com"]}]}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(policy_data, f, ensure_ascii=False)
            temp_path = f.name

        try:
            policy = load_policy_from_json(temp_path)
            assert "user:tëst@éxample.com" in policy.bindings[0].members
        finally:
            os.unlink(temp_path)

    def test_load_policy_very_large(self):
        """Test loading policy with many bindings."""
        bindings = []
        for i in range(100):
            bindings.append(
                {"role": f"roles/custom.role{i}", "members": [f"user:user{i}@example.com"]}
            )

        policy_data = {"bindings": bindings}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy_data, f)
            temp_path = f.name

        try:
            policy = load_policy_from_json(temp_path)
            assert len(policy.bindings) == 100
        finally:
            os.unlink(temp_path)

    def test_load_policy_with_pathlib_path(self):
        """Test loading policy using pathlib.Path."""
        policy_data = {"bindings": [{"role": "roles/viewer", "members": ["user:test@example.com"]}]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy_data, f)
            temp_path = Path(f.name)

        try:
            policy = load_policy_from_json(str(temp_path))
            assert len(policy.bindings) == 1
        finally:
            temp_path.unlink()


class TestPolicyRoundtrip:
    """Tests for loading and saving policies."""

    def test_load_and_serialize_policy(self):
        """Test that loaded policy can be serialized back."""
        original_data = {
            "bindings": [
                {"role": "roles/owner", "members": ["user:admin@example.com"]},
                {"role": "roles/viewer", "members": ["user:viewer@example.com"]},
            ],
            "etag": "test-etag",
            "version": 1,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(original_data, f)
            temp_path = f.name

        try:
            # Load policy
            policy = load_policy_from_json(temp_path)

            # Serialize back to dict
            serialized = policy.model_dump()

            # Verify structure is maintained
            assert len(serialized["bindings"]) == 2
            assert serialized["etag"] == "test-etag"
            assert serialized["version"] == 1
        finally:
            os.unlink(temp_path)
