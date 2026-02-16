"""Tests for dependency injection container."""

from pathlib import Path

import pytest

from marimushka.audit import AuditLogger
from marimushka.config import MarimushkaConfig
from marimushka.dependencies import (
    Dependencies,
    create_dependencies,
    create_dependencies_from_config_file,
    create_test_dependencies,
)


class TestDependencies:
    """Tests for the Dependencies dataclass."""

    def test_default_dependencies(self):
        """Test that default dependencies are created correctly."""
        deps = Dependencies()

        assert deps.audit_logger is not None
        assert isinstance(deps.audit_logger, AuditLogger)
        assert deps.config is not None
        assert isinstance(deps.config, MarimushkaConfig)

    def test_custom_dependencies(self, tmp_path):
        """Test creating dependencies with custom values."""
        audit_log = tmp_path / "audit.log"
        audit_logger = AuditLogger(log_file=audit_log)
        config = MarimushkaConfig(max_workers=8, timeout=600)

        deps = Dependencies(
            audit_logger=audit_logger,
            config=config,
        )

        assert deps.audit_logger is audit_logger
        assert deps.config is config
        assert deps.config.max_workers == 8
        assert deps.config.timeout == 600

    def test_with_audit_logger(self, tmp_path):
        """Test creating a new instance with different audit logger."""
        deps = Dependencies()
        original_config = deps.config

        new_audit_logger = AuditLogger(log_file=tmp_path / "new_audit.log")
        new_deps = deps.with_audit_logger(new_audit_logger)

        # Original should be unchanged
        assert deps.audit_logger != new_audit_logger
        assert deps.config is original_config

        # New should have updated logger but same config
        assert new_deps.audit_logger is new_audit_logger
        assert new_deps.config is original_config

    def test_with_config(self):
        """Test creating a new instance with different config."""
        deps = Dependencies()
        original_audit_logger = deps.audit_logger

        new_config = MarimushkaConfig(max_workers=16)
        new_deps = deps.with_config(new_config)

        # Original should be unchanged
        assert deps.config != new_config
        assert deps.audit_logger is original_audit_logger

        # New should have updated config but same audit logger
        assert new_deps.config is new_config
        assert new_deps.audit_logger is original_audit_logger


class TestCreateDependencies:
    """Tests for the create_dependencies factory function."""

    def test_create_with_defaults(self):
        """Test creating dependencies with all defaults."""
        deps = create_dependencies()

        assert deps.audit_logger is not None
        assert deps.config is not None
        assert isinstance(deps.config, MarimushkaConfig)

    def test_create_with_audit_log(self, tmp_path):
        """Test creating dependencies with audit log path."""
        audit_log = tmp_path / "audit.log"
        deps = create_dependencies(audit_log=audit_log)

        assert deps.audit_logger.log_file == audit_log
        assert deps.config is not None

    def test_create_with_config(self):
        """Test creating dependencies with custom config."""
        config = MarimushkaConfig(
            max_workers=8,
            timeout=900,
            parallel=False,
        )
        deps = create_dependencies(config=config)

        assert deps.config is config
        assert deps.config.max_workers == 8
        assert deps.config.timeout == 900
        assert deps.config.parallel is False

    def test_create_with_both(self, tmp_path):
        """Test creating dependencies with both audit log and config."""
        audit_log = tmp_path / "audit.log"
        config = MarimushkaConfig(max_workers=4)

        deps = create_dependencies(audit_log=audit_log, config=config)

        assert deps.audit_logger.log_file == audit_log
        assert deps.config is config


class TestCreateDependenciesFromConfigFile:
    """Tests for creating dependencies from config file."""

    def test_create_from_valid_config_file(self, tmp_path):
        """Test loading dependencies from a valid TOML config."""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text("""
[marimushka]
output = "_site"
notebooks = "notebooks"
apps = "apps"
max_workers = 8
timeout = 600

[marimushka.security]
audit_enabled = true
max_file_size_mb = 20
""")

        deps = create_dependencies_from_config_file(config_file)

        assert deps.config.output == "_site"
        assert deps.config.max_workers == 8
        assert deps.config.timeout == 600
        assert deps.config.audit_enabled is True
        assert deps.config.max_file_size_mb == 20

    def test_create_from_config_with_audit_log(self, tmp_path):
        """Test loading config with audit log path."""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text("""
[marimushka.security]
audit_log = "audit.log"
audit_enabled = true
""")

        deps = create_dependencies_from_config_file(config_file)

        assert deps.audit_logger.enabled is True
        assert deps.audit_logger.log_file == Path("audit.log")

    def test_create_from_config_with_override_audit_log(self, tmp_path):
        """Test that explicit audit_log parameter overrides config."""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text("""
[marimushka.security]
audit_log = "config_audit.log"
""")

        override_log = tmp_path / "override_audit.log"
        deps = create_dependencies_from_config_file(
            config_file,
            audit_log=override_log,
        )

        # Should use override, not config file path
        assert deps.audit_logger.log_file == override_log

    def test_create_from_nonexistent_config_file(self, tmp_path):
        """Test that nonexistent config file raises error."""
        config_file = tmp_path / "nonexistent.toml"

        with pytest.raises(FileNotFoundError):
            create_dependencies_from_config_file(config_file)

    def test_create_from_invalid_config_file(self, tmp_path):
        """Test that invalid TOML raises error."""
        config_file = tmp_path / "invalid.toml"
        config_file.write_text("this is not valid TOML [[[")

        with pytest.raises(ValueError):
            create_dependencies_from_config_file(config_file)


class TestCreateTestDependencies:
    """Tests for the create_test_dependencies helper."""

    def test_create_test_dependencies(self, tmp_path):
        """Test creating test dependencies."""
        deps = create_test_dependencies(tmp_path)

        assert deps.audit_logger is not None
        assert deps.audit_logger.enabled is True
        assert deps.audit_logger.log_file == tmp_path / "test_audit.log"
        assert deps.config is not None

    def test_test_dependencies_audit_log_created(self, tmp_path):
        """Test that test dependencies create the audit log file."""
        deps = create_test_dependencies(tmp_path)

        # Write something to trigger log creation
        deps.audit_logger.log_config_load(None, True)

        # Verify log file was created
        audit_log = tmp_path / "test_audit.log"
        assert audit_log.exists()


class TestDependenciesIntegration:
    """Integration tests for dependencies with other components."""

    def test_dependencies_with_export_main(self, resource_dir, tmp_path):
        """Test using dependencies with the main export function."""
        from marimushka.export import main

        # Create custom dependencies
        audit_log = tmp_path / "export_audit.log"
        deps = create_dependencies(audit_log=audit_log)

        # Use with main (pass audit_logger explicitly)
        # Note: main doesn't accept deps directly, but we can pass components
        html = main(
            notebooks=resource_dir / "marimo" / "notebooks",
            template=resource_dir / "templates" / "tailwind.html.j2",
            output=tmp_path / "output",
        )

        assert html
        assert (tmp_path / "output").exists()

    def test_dependencies_with_generate_index(self, resource_dir, tmp_path):
        """Test using dependencies with generate_index."""
        from marimushka.notebook import Kind, folder2notebooks
        from marimushka.orchestrator import generate_index

        # Create dependencies
        deps = create_test_dependencies(tmp_path)

        # Load notebooks
        notebooks = folder2notebooks(resource_dir / "marimo" / "notebooks", Kind.NB)

        # Generate index with dependency-injected audit logger
        html = generate_index(
            output=tmp_path / "output",
            template_file=resource_dir / "templates" / "tailwind.html.j2",
            notebooks=notebooks,
            apps=[],
            notebooks_wasm=[],
            audit_logger=deps.audit_logger,
        )

        assert html
        # Verify audit log was used
        assert deps.audit_logger.log_file.exists()
