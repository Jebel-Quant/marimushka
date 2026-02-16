"""Dependency injection container for marimushka.

This module provides a dependency container pattern that encapsulates all
injectable dependencies used throughout the application. This makes it easier
to manage dependencies, test components in isolation, and customize behavior.

Example::

    from marimushka.dependencies import Dependencies, create_dependencies

    # Use default dependencies
    deps = create_dependencies()

    # Or customize for testing/special cases
    from marimushka.audit import AuditLogger
    from marimushka.config import MarimushkaConfig

    custom_audit = AuditLogger(log_file=Path("custom_audit.log"))
    custom_config = MarimushkaConfig(max_workers=8, timeout=600)

    deps = Dependencies(
        audit_logger=custom_audit,
        config=custom_config
    )

    # Use in application
    from marimushka.export import main_with_deps
    html = main_with_deps(deps, notebooks="notebooks", apps="apps")

"""

from dataclasses import dataclass, field
from pathlib import Path

from .audit import AuditLogger, get_audit_logger
from .config import MarimushkaConfig


@dataclass
class Dependencies:
    """Container for all injectable dependencies.

    This class holds all dependencies that can be injected throughout the
    application, providing a single point of configuration and making it
    easy to customize behavior for testing or special use cases.

    Attributes:
        audit_logger: Logger for security-relevant audit events.
        config: Configuration settings for export behavior.

    Example::

        from marimushka.dependencies import Dependencies
        from marimushka.audit import AuditLogger
        from marimushka.config import MarimushkaConfig

        # Create custom dependencies
        deps = Dependencies(
            audit_logger=AuditLogger(log_file=Path("my_audit.log")),
            config=MarimushkaConfig(max_workers=8)
        )

        # Use with export functions
        from marimushka.orchestrator import generate_index
        html = generate_index(
            output=Path("_site"),
            template_file=Path("template.html.j2"),
            notebooks=[],
            audit_logger=deps.audit_logger
        )

    """

    audit_logger: AuditLogger = field(default_factory=get_audit_logger)
    config: MarimushkaConfig = field(default_factory=MarimushkaConfig)

    def with_audit_logger(self, audit_logger: AuditLogger) -> "Dependencies":
        """Create a new Dependencies instance with a different audit logger.

        Args:
            audit_logger: The new audit logger to use.

        Returns:
            A new Dependencies instance with the specified audit logger.

        Example::

            from marimushka.dependencies import create_dependencies
            from marimushka.audit import AuditLogger
            from pathlib import Path

            deps = create_dependencies()
            test_deps = deps.with_audit_logger(
                AuditLogger(log_file=Path("test_audit.log"))
            )

        """
        return Dependencies(
            audit_logger=audit_logger,
            config=self.config,
        )

    def with_config(self, config: MarimushkaConfig) -> "Dependencies":
        """Create a new Dependencies instance with a different configuration.

        Args:
            config: The new configuration to use.

        Returns:
            A new Dependencies instance with the specified configuration.

        Example::

            from marimushka.dependencies import create_dependencies
            from marimushka.config import MarimushkaConfig

            deps = create_dependencies()
            prod_deps = deps.with_config(
                MarimushkaConfig(max_workers=16, timeout=900)
            )

        """
        return Dependencies(
            audit_logger=self.audit_logger,
            config=config,
        )


def create_dependencies(
    audit_log: Path | None = None,
    config: MarimushkaConfig | None = None,
) -> Dependencies:
    """Create a Dependencies container with optional customization.

    This factory function provides a convenient way to create Dependencies
    with common customizations while falling back to sensible defaults.

    Args:
        audit_log: Optional path to audit log file. If provided, creates
                  an AuditLogger that writes to this file.
        config: Optional custom configuration. If None, uses default config.

    Returns:
        A Dependencies instance with the specified settings.

    Example::

        from pathlib import Path
        from marimushka.dependencies import create_dependencies
        from marimushka.config import MarimushkaConfig

        # Simple usage with audit log
        deps = create_dependencies(audit_log=Path("audit.log"))

        # With custom config
        config = MarimushkaConfig(max_workers=8, parallel=True)
        deps = create_dependencies(config=config)

        # With both
        deps = create_dependencies(
            audit_log=Path("audit.log"),
            config=MarimushkaConfig(timeout=600)
        )

    """
    if audit_log is not None:
        audit_logger = AuditLogger(log_file=audit_log)
    else:
        audit_logger = get_audit_logger()

    if config is None:
        config = MarimushkaConfig()

    return Dependencies(
        audit_logger=audit_logger,
        config=config,
    )


def create_dependencies_from_config_file(
    config_path: Path,
    audit_log: Path | None = None,
) -> Dependencies:
    """Create Dependencies by loading configuration from a TOML file.

    This function loads configuration from a file and creates a Dependencies
    container with it, optionally overriding the audit log path.

    Args:
        config_path: Path to the TOML configuration file.
        audit_log: Optional override for audit log path. If None, uses
                  the audit log path from the config file (if specified).

    Returns:
        A Dependencies instance with settings from the config file.

    Raises:
        FileNotFoundError: If config_path doesn't exist.
        ValueError: If the config file is invalid.

    Example::

        from pathlib import Path
        from marimushka.dependencies import create_dependencies_from_config_file

        # Load from config file
        deps = create_dependencies_from_config_file(
            Path(".marimushka.toml")
        )

        # Override audit log
        deps = create_dependencies_from_config_file(
            config_path=Path(".marimushka.toml"),
            audit_log=Path("custom_audit.log")
        )

    """
    config = MarimushkaConfig.from_file(config_path)

    # Determine audit log path
    if audit_log is not None:
        # Use explicit override
        audit_log_path = audit_log
    elif config.audit_log is not None:
        # Use path from config
        audit_log_path = Path(config.audit_log)
    else:
        # No audit log file
        audit_log_path = None

    # Create audit logger
    if audit_log_path is not None:
        audit_logger = AuditLogger(
            enabled=config.audit_enabled,
            log_file=audit_log_path,
        )
    else:
        audit_logger = AuditLogger(enabled=config.audit_enabled)

    return Dependencies(
        audit_logger=audit_logger,
        config=config,
    )


def create_test_dependencies(tmp_dir: Path) -> Dependencies:
    """Create Dependencies suitable for testing.

    This function creates a Dependencies container configured for testing,
    with audit logging to a temporary file and default configuration.

    Args:
        tmp_dir: Temporary directory for test artifacts.

    Returns:
        A Dependencies instance configured for testing.

    Example::

        from pathlib import Path
        from marimushka.dependencies import create_test_dependencies

        def test_something(tmp_path):
            deps = create_test_dependencies(tmp_path)
            # Use deps in your test...

    """
    audit_log = tmp_dir / "test_audit.log"
    return Dependencies(
        audit_logger=AuditLogger(enabled=True, log_file=audit_log),
        config=MarimushkaConfig(),
    )
