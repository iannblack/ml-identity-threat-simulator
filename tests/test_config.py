"""
Comprehensive tests for core.config module.
Tests configuration loading, validation, and fallback behavior.
"""

import os
import tempfile

import pytest
import yaml

from src.core.config import AppConfig


class TestAppConfigCreation:
    """Tests for AppConfig model creation."""

    def test_config_creation_with_defaults(self):
        """Test creating config with explicit values."""
        config = AppConfig(
            risky_roles=["roles/owner", "roles/editor"],
            wildcard_members=["allUsers", "allAuthenticatedUsers"],
        )
        assert "roles/owner" in config.risky_roles
        assert "allUsers" in config.wildcard_members

    def test_config_creation_custom_roles(self):
        """Test creating config with custom risky roles."""
        custom_roles = [
            "roles/owner",
            "roles/editor",
            "roles/bigquery.admin",
            "roles/storage.admin",
            "roles/iam.securityAdmin",
        ]
        config = AppConfig(risky_roles=custom_roles, wildcard_members=["allUsers"])
        assert len(config.risky_roles) == 5
        assert "roles/bigquery.admin" in config.risky_roles

    def test_config_creation_custom_wildcards(self):
        """Test creating config with custom wildcard members."""
        custom_wildcards = ["allUsers", "allAuthenticatedUsers", "domain:example.com"]
        config = AppConfig(risky_roles=["roles/owner"], wildcard_members=custom_wildcards)
        assert len(config.wildcard_members) == 3
        assert "domain:example.com" in config.wildcard_members

    def test_config_empty_lists(self):
        """Test config with empty lists (edge case)."""
        config = AppConfig(risky_roles=[], wildcard_members=[])
        assert config.risky_roles == []
        assert config.wildcard_members == []


class TestAppConfigLoad:
    """Tests for AppConfig.load() classmethod."""

    def test_load_from_nonexistent_file(self):
        """Test loading config when file doesn't exist returns defaults."""
        config = AppConfig.load("nonexistent_config.yaml")

        # Should return fallback defaults
        assert "roles/owner" in config.risky_roles
        assert "roles/editor" in config.risky_roles
        assert "allUsers" in config.wildcard_members
        assert "allAuthenticatedUsers" in config.wildcard_members

    def test_load_from_valid_yaml(self):
        """Test loading config from valid YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml_content = {
                "risky_roles": ["roles/owner", "roles/editor", "roles/admin"],
                "wildcard_members": ["allUsers", "allAuthenticatedUsers", "domain:test.com"],
            }
            yaml.dump(yaml_content, f)
            temp_path = f.name

        try:
            config = AppConfig.load(temp_path)
            assert len(config.risky_roles) == 3
            assert "roles/admin" in config.risky_roles
            assert "domain:test.com" in config.wildcard_members
        finally:
            os.unlink(temp_path)

    def test_load_from_minimal_yaml(self):
        """Test loading config with minimal YAML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml_content = {"risky_roles": ["roles/owner"], "wildcard_members": ["allUsers"]}
            yaml.dump(yaml_content, f)
            temp_path = f.name

        try:
            config = AppConfig.load(temp_path)
            assert len(config.risky_roles) == 1
            assert len(config.wildcard_members) == 1
        finally:
            os.unlink(temp_path)

    def test_load_from_yaml_with_extra_fields(self):
        """Test loading YAML with extra fields (should be ignored)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml_content = {
                "risky_roles": ["roles/owner"],
                "wildcard_members": ["allUsers"],
                "logging": {"level": "INFO", "format": "%(message)s"},
                "extra_field": "should be ignored",
            }
            yaml.dump(yaml_content, f)
            temp_path = f.name

        try:
            config = AppConfig.load(temp_path)
            # Should load successfully, ignoring extra fields
            assert "roles/owner" in config.risky_roles
        finally:
            os.unlink(temp_path)

    def test_load_from_empty_yaml(self):
        """Test loading from empty YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            # Empty YAML should cause validation error
            with pytest.raises(Exception):  # Pydantic ValidationError
                AppConfig.load(temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_default_path(self):
        """Test loading with default path."""
        # This will try to load config.yaml from current directory
        # If it doesn't exist, should return defaults
        config = AppConfig.load()

        # Should either load from config.yaml or return defaults
        assert isinstance(config.risky_roles, list)
        assert isinstance(config.wildcard_members, list)


class TestAppConfigValidation:
    """Tests for AppConfig validation."""

    def test_config_requires_risky_roles(self):
        """Test that config requires risky_roles field."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            AppConfig(wildcard_members=["allUsers"])

    def test_config_requires_wildcard_members(self):
        """Test that config requires wildcard_members field."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            AppConfig(risky_roles=["roles/owner"])

    def test_config_risky_roles_must_be_list(self):
        """Test that risky_roles must be a list."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            AppConfig(
                risky_roles="roles/owner",  # Should be list, not string
                wildcard_members=["allUsers"],
            )

    def test_config_wildcard_members_must_be_list(self):
        """Test that wildcard_members must be a list."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            AppConfig(
                risky_roles=["roles/owner"],
                wildcard_members="allUsers",  # Should be list, not string
            )


class TestAppConfigSerialization:
    """Tests for AppConfig serialization."""

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = AppConfig(
            risky_roles=["roles/owner", "roles/editor"], wildcard_members=["allUsers"]
        )
        config_dict = config.model_dump()

        assert "risky_roles" in config_dict
        assert "wildcard_members" in config_dict
        assert isinstance(config_dict["risky_roles"], list)

    def test_config_to_json(self):
        """Test converting config to JSON."""
        config = AppConfig(risky_roles=["roles/owner"], wildcard_members=["allUsers"])
        config_json = config.model_dump_json()

        assert isinstance(config_json, str)
        assert "risky_roles" in config_json
        assert "wildcard_members" in config_json


class TestAppConfigIntegration:
    """Integration tests for AppConfig."""

    def test_load_and_modify_config(self):
        """Test loading config and modifying it."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml_content = {"risky_roles": ["roles/owner"], "wildcard_members": ["allUsers"]}
            yaml.dump(yaml_content, f)
            temp_path = f.name

        try:
            config = AppConfig.load(temp_path)

            # Modify config (create new instance)
            modified_config = AppConfig(
                risky_roles=config.risky_roles + ["roles/editor"],
                wildcard_members=config.wildcard_members,
            )

            assert len(modified_config.risky_roles) == 2
            assert "roles/editor" in modified_config.risky_roles
        finally:
            os.unlink(temp_path)

    def test_config_with_real_gcp_roles(self):
        """Test config with realistic GCP roles."""
        gcp_roles = [
            "roles/owner",
            "roles/editor",
            "roles/viewer",
            "roles/bigquery.admin",
            "roles/bigquery.dataEditor",
            "roles/storage.admin",
            "roles/storage.objectAdmin",
            "roles/iam.securityAdmin",
            "roles/iam.serviceAccountAdmin",
        ]

        config = AppConfig(
            risky_roles=gcp_roles, wildcard_members=["allUsers", "allAuthenticatedUsers"]
        )

        assert len(config.risky_roles) == 9
        assert "roles/bigquery.admin" in config.risky_roles
        assert "roles/iam.securityAdmin" in config.risky_roles

    def test_config_roundtrip_yaml(self):
        """Test saving and loading config maintains data."""
        original_config = AppConfig(
            risky_roles=["roles/owner", "roles/editor", "roles/admin"],
            wildcard_members=["allUsers", "allAuthenticatedUsers", "domain:test.com"],
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(original_config.model_dump(), f)
            temp_path = f.name

        try:
            loaded_config = AppConfig.load(temp_path)

            assert loaded_config.risky_roles == original_config.risky_roles
            assert loaded_config.wildcard_members == original_config.wildcard_members
        finally:
            os.unlink(temp_path)


class TestAppConfigEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_config_with_duplicate_roles(self):
        """Test config handles duplicate roles."""
        config = AppConfig(
            risky_roles=["roles/owner", "roles/owner", "roles/editor"],
            wildcard_members=["allUsers"],
        )
        # Duplicates are allowed (list doesn't enforce uniqueness)
        assert len(config.risky_roles) == 3

    def test_config_with_very_long_lists(self):
        """Test config with many roles."""
        many_roles = [f"roles/custom_{i}" for i in range(100)]
        config = AppConfig(risky_roles=many_roles, wildcard_members=["allUsers"])
        assert len(config.risky_roles) == 100

    def test_config_with_special_characters(self):
        """Test config with special characters in role names."""
        config = AppConfig(
            risky_roles=["roles/custom-role_123", "roles/test.role"],
            wildcard_members=["domain:example.com", "user:test@example.com"],
        )
        assert "roles/custom-role_123" in config.risky_roles
        assert "domain:example.com" in config.wildcard_members
