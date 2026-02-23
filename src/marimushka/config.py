"""Configuration management for marimushka.

This module provides configuration loading and validation from TOML files.
"""

import tomllib
from pathlib import Path
from typing import Any


class MarimushkaConfig:
    """Configuration for marimushka.

    This class encapsulates all configuration options with sensible defaults.

    Attributes:
        output: Output directory for exported files.
        template: Path to Jinja2 template file.
        notebooks: Directory containing static notebooks.
        apps: Directory containing app notebooks.
        notebooks_wasm: Directory containing interactive notebooks.
        sandbox: Whether to run exports in sandbox mode.
        parallel: Whether to export notebooks in parallel.
        max_workers: Maximum number of parallel workers.
        timeout: Timeout in seconds for each export.
        audit_log: Optional path to audit log file.
        audit_enabled: Whether audit logging is enabled.
        max_file_size_mb: Maximum file size in MB for templates/notebooks.
        file_permissions: Default file permissions (octal).

    """

    def __init__(
        self,
        output: str = "_site",
        template: str | None = None,
        notebooks: str = "notebooks",
        apps: str = "apps",
        notebooks_wasm: str = "notebooks_wasm",
        sandbox: bool = True,
        parallel: bool = True,
        max_workers: int = 4,
        timeout: int = 300,
        audit_log: str | None = None,
        audit_enabled: bool = True,
        max_file_size_mb: int = 10,
        file_permissions: int = 0o644,
    ) -> None:
        """Initialize configuration with defaults.

        Args:
            output: Output directory. Defaults to "_site".
            template: Template path. Defaults to None (uses built-in).
            notebooks: Notebooks directory. Defaults to "notebooks".
            apps: Apps directory. Defaults to "apps".
            notebooks_wasm: Interactive notebooks directory. Defaults to "notebooks_wasm".
            sandbox: Use sandbox mode. Defaults to True.
            parallel: Use parallel export. Defaults to True.
            max_workers: Max parallel workers. Defaults to 4.
            timeout: Export timeout. Defaults to 300.
            audit_log: Audit log file path. Defaults to None.
            audit_enabled: Enable audit logging. Defaults to True.
            max_file_size_mb: Max file size in MB. Defaults to 10.
            file_permissions: File permissions. Defaults to 0o644.

        """
        self.output = output
        self.template = template
        self.notebooks = notebooks
        self.apps = apps
        self.notebooks_wasm = notebooks_wasm
        self.sandbox = sandbox
        self.parallel = parallel
        self.max_workers = max_workers
        self.timeout = timeout
        self.audit_log = audit_log
        self.audit_enabled = audit_enabled
        self.max_file_size_mb = max_file_size_mb
        self.file_permissions = file_permissions

    @classmethod
    def from_file(cls, config_path: Path) -> "MarimushkaConfig":
        """Load configuration from a TOML file.

        Args:
            config_path: Path to the configuration file.

        Returns:
            A MarimushkaConfig instance with loaded settings.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            ValueError: If config file is invalid.

        """
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")  # noqa: TRY003

        try:
            with config_path.open("rb") as f:
                config_data = tomllib.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse config file: {e}") from e  # noqa: TRY003

        # Extract marimushka section
        marimushka_config = config_data.get("marimushka", {})

        # Handle security subsection
        security_config = marimushka_config.get("security", {})

        return cls(
            output=marimushka_config.get("output", "_site"),
            template=marimushka_config.get("template"),
            notebooks=marimushka_config.get("notebooks", "notebooks"),
            apps=marimushka_config.get("apps", "apps"),
            notebooks_wasm=marimushka_config.get("notebooks_wasm", "notebooks_wasm"),
            sandbox=marimushka_config.get("sandbox", True),
            parallel=marimushka_config.get("parallel", True),
            max_workers=marimushka_config.get("max_workers", 4),
            timeout=marimushka_config.get("timeout", 300),
            audit_log=security_config.get("audit_log"),
            audit_enabled=security_config.get("audit_enabled", True),
            max_file_size_mb=security_config.get("max_file_size_mb", 10),
            file_permissions=int(str(security_config.get("file_permissions", "0o644")), 8),
        )

    @classmethod
    def from_file_or_defaults(cls, config_path: Path | None = None) -> "MarimushkaConfig":
        """Load configuration from file if it exists, otherwise use defaults.

        Args:
            config_path: Optional path to config file. If None, looks for
                        .marimushka.toml in current directory.

        Returns:
            A MarimushkaConfig instance.

        """
        if config_path is None:
            config_path = Path(".marimushka.toml")

        if config_path.exists():
            return cls.from_file(config_path)

        return cls()

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration.

        """
        return {
            "output": self.output,
            "template": self.template,
            "notebooks": self.notebooks,
            "apps": self.apps,
            "notebooks_wasm": self.notebooks_wasm,
            "sandbox": self.sandbox,
            "parallel": self.parallel,
            "max_workers": self.max_workers,
            "timeout": self.timeout,
            "security": {
                "audit_log": self.audit_log,
                "audit_enabled": self.audit_enabled,
                "max_file_size_mb": self.max_file_size_mb,
                "file_permissions": oct(self.file_permissions),
            },
        }
