"""Tests for the config module."""

import pytest

from marimushka.config import MarimushkaConfig


class TestMarimushkaConfig:
    """Tests for MarimushkaConfig class."""

    def test_default_initialization(self):
        """Test default config initialization."""
        # Execute
        config = MarimushkaConfig()

        # Assert
        assert config.output == "_site"
        assert config.template is None
        assert config.notebooks == "notebooks"
        assert config.apps == "apps"
        assert config.notebooks_wasm == "notebooks_wasm"
        assert config.sandbox is True
        assert config.parallel is True
        assert config.max_workers == 4
        assert config.timeout == 300
        assert config.audit_enabled is True
        assert config.max_file_size_mb == 10
        assert config.file_permissions == 0o644

    def test_custom_initialization(self):
        """Test custom config initialization."""
        # Execute
        config = MarimushkaConfig(
            output="dist",
            template="custom.html.j2",
            notebooks="my_notebooks",
            max_workers=8,
            audit_log="audit.log",
        )

        # Assert
        assert config.output == "dist"
        assert config.template == "custom.html.j2"
        assert config.notebooks == "my_notebooks"
        assert config.max_workers == 8
        assert config.audit_log == "audit.log"

    def test_from_file(self, tmp_path):
        """Test loading config from file."""
        # Setup
        config_file = tmp_path / ".marimushka.toml"
        config_file.write_text(
            """
[marimushka]
output = "public"
notebooks = "nbs"
apps = "applications"
sandbox = false
max_workers = 8

[marimushka.security]
audit_enabled = true
audit_log = "audit.log"
max_file_size_mb = 20
file_permissions = "0o600"
"""
        )

        # Execute
        config = MarimushkaConfig.from_file(config_file)

        # Assert
        assert config.output == "public"
        assert config.notebooks == "nbs"
        assert config.apps == "applications"
        assert config.sandbox is False
        assert config.max_workers == 8
        assert config.audit_enabled is True
        assert config.audit_log == "audit.log"
        assert config.max_file_size_mb == 20
        assert config.file_permissions == 0o600

    def test_from_file_not_found(self, tmp_path):
        """Test loading config from non-existent file."""
        # Setup
        config_file = tmp_path / "nonexistent.toml"

        # Execute & Assert
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            MarimushkaConfig.from_file(config_file)

    def test_from_file_invalid(self, tmp_path):
        """Test loading invalid config file."""
        # Setup
        config_file = tmp_path / "invalid.toml"
        config_file.write_text("invalid toml {{{")

        # Execute & Assert
        with pytest.raises(ValueError, match="Failed to parse config file"):
            MarimushkaConfig.from_file(config_file)

    def test_from_file_or_defaults_with_file(self, tmp_path, monkeypatch):
        """Test loading config with existing file."""
        # Setup
        config_file = tmp_path / ".marimushka.toml"
        config_file.write_text(
            """
[marimushka]
output = "custom_site"
"""
        )
        monkeypatch.chdir(tmp_path)

        # Execute
        config = MarimushkaConfig.from_file_or_defaults()

        # Assert
        assert config.output == "custom_site"

    def test_from_file_or_defaults_without_file(self, tmp_path, monkeypatch):
        """Test loading config without file uses defaults."""
        # Setup
        monkeypatch.chdir(tmp_path)

        # Execute
        config = MarimushkaConfig.from_file_or_defaults()

        # Assert
        assert config.output == "_site"  # Default value

    def test_to_dict(self):
        """Test converting config to dictionary."""
        # Setup
        config = MarimushkaConfig(
            output="dist",
            max_workers=8,
            audit_log="audit.log",
        )

        # Execute
        config_dict = config.to_dict()

        # Assert
        assert config_dict["output"] == "dist"
        assert config_dict["max_workers"] == 8
        assert config_dict["security"]["audit_log"] == "audit.log"
        assert "0o644" in config_dict["security"]["file_permissions"]
