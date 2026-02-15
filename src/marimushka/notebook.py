"""Notebook module for handling marimo notebooks.

This module provides the core abstractions for representing and exporting marimo
notebooks to various HTML and WebAssembly formats. It defines the Notebook class
which encapsulates a marimo notebook file and handles the export process via
subprocess calls to the marimo CLI.

Key Components:
    Kind: Enumeration of notebook export types (static HTML, interactive WASM, app mode).
    Notebook: Dataclass representing a single marimo notebook with export capabilities.
    folder2notebooks: Utility function to discover notebooks in a directory.

Export Modes:
    The module supports three export modes through the Kind enum:

    - NB (notebook): Exports to static HTML using `marimo export html --sandbox`.
      Best for documentation and read-only sharing.

    - NB_WASM (notebook_wasm): Exports to interactive WebAssembly using
      `marimo export html-wasm --mode edit --sandbox`. Users can edit and run
      code in the browser.

    - APP (app): Exports to WebAssembly in run mode using
      `marimo export html-wasm --mode run --no-show-code --sandbox`. Presents
      a clean application interface with code hidden.

Example::

    from marimushka.notebook import Notebook, Kind, folder2notebooks
    from pathlib import Path

    # Create a notebook and export it
    nb = Notebook(Path("my_notebook.py"), kind=Kind.APP)
    result = nb.export(Path("_site/apps"))
    if result.success:
        print(f"Exported to {result.output_path}")

    # Discover all notebooks in a directory
    notebooks = folder2notebooks(Path("notebooks"), kind=Kind.NB)
"""

import dataclasses
import os
import shutil
import subprocess  # nosec B404
from enum import Enum
from pathlib import Path

from loguru import logger

from .audit import AuditLogger, get_audit_logger
from .exceptions import (
    ExportError,
    ExportExecutableNotFoundError,
    ExportSubprocessError,
    NotebookExportResult,
    NotebookInvalidError,
    NotebookNotFoundError,
)
from .security import sanitize_error_message, set_secure_file_permissions, validate_bin_path, validate_path_traversal


class Kind(Enum):
    """Enumeration of notebook export types.

    This enum defines the three ways a marimo notebook can be exported,
    each with different capabilities and use cases. The choice of Kind
    affects both the marimo export command used and the output directory.

    Attributes:
        NB: Static HTML export. Creates a read-only HTML representation
            of the notebook. Output goes to the 'notebooks/' subdirectory.
            Uses command: `marimo export html --sandbox`
        NB_WASM: Interactive WebAssembly export in edit mode. Creates a
            fully interactive notebook that runs in the browser with code
            editing capabilities. Output goes to the 'notebooks_wasm/'
            subdirectory. Uses command: `marimo export html-wasm --mode edit --sandbox`
        APP: WebAssembly export in run/app mode. Creates an application
            interface with code hidden from users. Ideal for dashboards
            and user-facing tools. Output goes to the 'apps/' subdirectory.
            Uses command: `marimo export html-wasm --mode run --no-show-code --sandbox`

    """

    NB = "notebook"
    NB_WASM = "notebook_wasm"
    APP = "app"

    @classmethod
    def from_str(cls, value: str) -> "Kind":
        """Represent a factory method to parse a string into a Kind enumeration instance.

        This method attempts to match the input string to an existing kind defined
        in the Kind enumeration. If the input string does not match any valid kind,
        an error is raised detailing the invalid value and listing acceptable kinds.

        Args:
            value (str): A string representing the kind to parse into a Kind instance.

        Returns:
            Kind: An instance of the Kind enumeration corresponding to the input string.

        Raises:
            ValueError: If the input string does not match any valid Kind value.

        Examples:
            >>> from marimushka.notebook import Kind
            >>> Kind.from_str("notebook")
            <Kind.NB: 'notebook'>
            >>> Kind.from_str("app")
            <Kind.APP: 'app'>
            >>> Kind.from_str("invalid")
            Traceback (most recent call last):
                ...
            ValueError: Invalid Kind: 'invalid'. Must be one of ['notebook', 'notebook_wasm', 'app']

        """
        try:
            return Kind(value)
        except ValueError as e:
            msg = f"Invalid Kind: {value!r}. Must be one of {[k.value for k in Kind]}"
            raise ValueError(msg) from e

    @property
    def command(self) -> list[str]:
        """Get the command list associated with a specific Kind instance.

        The command property returns a list of command strings that correspond
        to different kinds of operations based on the Kind instance.

        Attributes:
            command: A list of strings representing the command.

        Returns:
            list[str]: A list of command strings for the corresponding Kind instance.

        Examples:
            >>> from marimushka.notebook import Kind
            >>> Kind.NB.command
            ['marimo', 'export', 'html']
            >>> Kind.APP.command
            ['marimo', 'export', 'html-wasm', '--mode', 'run', '--no-show-code']

        """
        commands = {
            Kind.NB: ["marimo", "export", "html"],
            Kind.NB_WASM: ["marimo", "export", "html-wasm", "--mode", "edit"],
            Kind.APP: ["marimo", "export", "html-wasm", "--mode", "run", "--no-show-code"],
        }
        return commands[self]

    @property
    def html_path(self) -> Path:
        """Provide a property to determine the HTML path for different kinds of objects.

        This property computes the corresponding directory path based on the kind
        of the object, such as notebooks, notebooks_wasm, or apps.

        @return: A Path object representing the relevant directory path for the
            current kind.

        @rtype: Path

        Examples:
            >>> from marimushka.notebook import Kind
            >>> str(Kind.NB.html_path)
            'notebooks'
            >>> str(Kind.APP.html_path)
            'apps'

        """
        paths = {
            Kind.NB: Path("notebooks"),
            Kind.NB_WASM: Path("notebooks_wasm"),
            Kind.APP: Path("apps"),
        }
        return paths[self]


@dataclasses.dataclass(frozen=True)
class Notebook:
    """Represents a marimo notebook.

    This class encapsulates a marimo notebook (.py file) and provides methods
    for exporting it to HTML/WebAssembly format.

    Attributes:
        path (Path): Path to the marimo notebook (.py file)
        kind (Kind): How the notebook ts treated

    """

    path: Path
    kind: Kind = Kind.NB

    def __post_init__(self) -> None:
        """Validate the notebook path after initialization.

        Raises:
            NotebookNotFoundError: If the file does not exist.
            NotebookInvalidError: If the path is not a file or not a Python file.

        """
        if not self.path.exists():
            raise NotebookNotFoundError(self.path)
        if not self.path.is_file():
            raise NotebookInvalidError(self.path, reason="path is not a file")
        if not self.path.suffix == ".py":
            raise NotebookInvalidError(self.path, reason="not a Python file")

    def export(
        self,
        output_dir: Path,
        sandbox: bool = True,
        bin_path: Path | None = None,
        timeout: int = 300,
    ) -> NotebookExportResult:
        """Export the notebook to HTML/WebAssembly format.

        This method exports the marimo notebook to HTML/WebAssembly format.
        If is_app is True, the notebook is exported in "run" mode with code hidden,
        suitable for applications. Otherwise, it's exported in "edit" mode,
        suitable for interactive notebooks.

        Args:
            output_dir: Directory where the exported HTML file will be saved.
            sandbox: Whether to run the notebook in a sandbox. Defaults to True.
            bin_path: The directory where the executable is located. Defaults to None.
            timeout: Maximum time in seconds for the export process. Defaults to 300.

        Returns:
            NotebookExportResult indicating success or failure with details.

        """
        audit_logger = get_audit_logger()

        # Resolve executable
        exe = self._resolve_executable(bin_path, audit_logger)
        if isinstance(exe, NotebookExportResult):
            return exe

        # Prepare output path
        output_file_or_error = self._prepare_output_path(output_dir, audit_logger)
        if isinstance(output_file_or_error, NotebookExportResult):
            return output_file_or_error
        output_file = output_file_or_error

        # Build and run command
        cmd = self._build_command(exe, sandbox, output_file)
        return self._run_export_subprocess(cmd, output_file, timeout, audit_logger)

    def _resolve_executable(self, bin_path: Path | None, audit_logger: AuditLogger) -> str | NotebookExportResult:
        """Resolve the executable path.

        Args:
            bin_path: Optional directory where the executable is located.
            audit_logger: Audit logger for security logging.

        Returns:
            Executable string on success, or NotebookExportResult on error.

        """
        executable = "uvx"

        if not bin_path:
            return executable

        # Validate bin_path for security
        try:
            validated_bin_path = validate_bin_path(bin_path)
            audit_logger.log_path_validation(bin_path, "bin_path", True)
        except ValueError as e:
            err: ExportError = ExportExecutableNotFoundError(executable, bin_path)
            sanitized_error = sanitize_error_message(str(e))
            logger.error(f"Invalid bin_path: {sanitized_error}")
            audit_logger.log_path_validation(bin_path, "bin_path", False, sanitized_error)
            return NotebookExportResult.failed(self.path, err)

        # Construct the full executable path
        # Use shutil.which to find it with platform-specific extensions (like .exe on Windows)
        exe = shutil.which(executable, path=str(validated_bin_path))
        if not exe:
            # Fallback: try constructing the path directly
            exe_path = validated_bin_path / executable
            if exe_path.is_file() and os.access(exe_path, os.X_OK):
                return str(exe_path)

            err = ExportExecutableNotFoundError(executable, validated_bin_path)
            logger.error(str(err))
            audit_logger.log_export(self.path, None, False, str(err))
            return NotebookExportResult.failed(self.path, err)

        return exe

    def _prepare_output_path(self, output_dir: Path, audit_logger: AuditLogger) -> Path | NotebookExportResult:
        """Validate and prepare the output path.

        Args:
            output_dir: Directory where the exported HTML file will be saved.
            audit_logger: Audit logger for security logging.

        Returns:
            Output file Path on success, or NotebookExportResult on error.

        """
        output_file = output_dir / f"{self.path.stem}.html"

        # Validate output path to prevent path traversal
        try:
            validate_path_traversal(output_file)
            audit_logger.log_path_validation(output_file, "output_path", True)
        except ValueError as e:
            sanitized_error = sanitize_error_message(str(e))
            err = ExportSubprocessError(
                notebook_path=self.path,
                command=[],  # Command not yet built
                return_code=-1,
                stderr=f"Invalid output path: {sanitized_error}",
            )
            logger.error(str(err))
            audit_logger.log_path_validation(output_file, "output_path", False, sanitized_error)
            return NotebookExportResult.failed(self.path, err)

        # Create output directory
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:  # pragma: no cover
            sanitized_error = sanitize_error_message(str(e))
            err = ExportSubprocessError(
                notebook_path=self.path,
                command=[],  # Command not yet built
                return_code=-1,
                stderr=f"Failed to create output directory: {sanitized_error}",
            )
            logger.error(str(err))
            audit_logger.log_export(self.path, None, False, sanitized_error)
            return NotebookExportResult.failed(self.path, err)

        return output_file

    def _build_command(self, exe: str, sandbox: bool, output_file: Path) -> list[str]:
        """Build the export command.

        Args:
            exe: Executable to use (e.g., 'uvx' or full path).
            sandbox: Whether to run the notebook in a sandbox.
            output_file: Path where the exported HTML file will be saved.

        Returns:
            Command list ready for subprocess execution.

        """
        cmd = [exe, *self.kind.command]
        if sandbox:
            cmd.append("--sandbox")
        else:
            cmd.append("--no-sandbox")
        cmd.extend([str(self.path), "-o", str(output_file)])
        return cmd

    def _run_export_subprocess(
        self, cmd: list[str], output_file: Path, timeout: int, audit_logger: AuditLogger
    ) -> NotebookExportResult:
        """Run the export subprocess and handle results.

        Args:
            cmd: Command list to execute.
            output_file: Path where the exported HTML file will be saved.
            timeout: Maximum time in seconds for the export process.
            audit_logger: Audit logger for security logging.

        Returns:
            NotebookExportResult indicating success or failure.

        """
        try:
            # Run marimo export command with timeout
            logger.debug(f"Running command: {cmd}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=timeout)  # nosec B603

            nb_logger = logger.bind(subprocess=f"[{self.path.name}] ")

            if result.stdout:
                nb_logger.info(f"stdout:\n{result.stdout.strip()}")

            if result.stderr:
                nb_logger.warning(f"stderr:\n{result.stderr.strip()}")

            if result.returncode != 0:
                sanitized_stderr = sanitize_error_message(result.stderr)
                err = ExportSubprocessError(
                    notebook_path=self.path,
                    command=cmd,
                    return_code=result.returncode,
                    stdout=result.stdout,
                    stderr=sanitized_stderr,
                )
                nb_logger.error(str(err))
                audit_logger.log_export(self.path, None, False, sanitized_stderr)
                return NotebookExportResult.failed(self.path, err)

            # Set secure permissions on output file
            try:
                set_secure_file_permissions(output_file, mode=0o644)
            except ValueError as e:  # pragma: no cover
                logger.warning(f"Could not set secure permissions on {output_file}: {e}")

            audit_logger.log_export(self.path, output_file, True)
            return NotebookExportResult.succeeded(self.path, output_file)

        except subprocess.TimeoutExpired:
            err = ExportSubprocessError(
                notebook_path=self.path,
                command=cmd,
                return_code=-1,
                stderr=f"Export timed out after {timeout} seconds",
            )
            logger.error(str(err))
            audit_logger.log_export(self.path, None, False, f"timeout after {timeout}s")
            return NotebookExportResult.failed(self.path, err)
        except FileNotFoundError as e:
            # Executable not found in PATH
            exec_err = ExportExecutableNotFoundError(cmd[0])
            sanitized_error = sanitize_error_message(str(e))
            logger.error(f"{exec_err}: {sanitized_error}")
            audit_logger.log_export(self.path, None, False, sanitized_error)
            return NotebookExportResult.failed(self.path, exec_err)
        except subprocess.SubprocessError as e:
            sanitized_error = sanitize_error_message(str(e))
            err = ExportSubprocessError(
                notebook_path=self.path,
                command=cmd,
                return_code=-1,
                stderr=sanitized_error,
            )
            logger.error(str(err))
            audit_logger.log_export(self.path, None, False, sanitized_error)
            return NotebookExportResult.failed(self.path, err)

    @property
    def display_name(self) -> str:
        """Return the display name for the notebook.

        The display name is derived from the notebook filename by replacing
        underscores with spaces, making it more human-readable.

        Returns:
            str: Human-friendly display name with underscores replaced by spaces.

        Examples:
            >>> # Demonstrating the transformation logic
            >>> filename = "my_cool_notebook"
            >>> display_name = filename.replace("_", " ")
            >>> display_name
            'my cool notebook'

        """
        return self.path.stem.replace("_", " ")

    @property
    def html_path(self) -> Path:
        """Return the path to the exported HTML file."""
        return self.kind.html_path / f"{self.path.stem}.html"


def folder2notebooks(folder: Path | str | None, kind: Kind = Kind.NB) -> list[Notebook]:
    """Discover and create Notebook instances for all Python files in a directory.

    This function scans a directory for Python files (*.py) and creates Notebook
    instances for each one. It assumes all Python files in the directory are
    valid marimo notebooks. The resulting list is sorted alphabetically by
    filename to ensure consistent ordering across runs.

    Args:
        folder: Path to the directory to scan for notebooks. Can be a Path
            object, a string path, or None. If None or empty string, returns
            an empty list.
        kind: The export type for all discovered notebooks. Defaults to Kind.NB
            (static HTML export). All notebooks in the folder will be assigned
            this kind.

    Returns:
        A list of Notebook instances, one for each Python file found in the
        directory, sorted alphabetically by filename. Returns an empty list
        if the folder is None, empty, or contains no Python files.

    Raises:
        NotebookNotFoundError: If a discovered file does not exist (unlikely
            in normal usage but possible in race conditions).
        NotebookInvalidError: If a discovered path is not a valid file.

    Example::

        from pathlib import Path
        from marimushka.notebook import folder2notebooks, Kind

        # Get all notebooks from a directory as static HTML exports
        notebooks = folder2notebooks(Path("notebooks"), Kind.NB)

        # Get all notebooks as interactive apps
        apps = folder2notebooks("apps", Kind.APP)

        # Handle empty or missing directories gracefully
        empty = folder2notebooks(None)  # Returns []
        empty = folder2notebooks("")    # Returns []

    Examples:
        >>> from marimushka.notebook import folder2notebooks
        >>> # When folder is None, returns empty list
        >>> folder2notebooks(None)
        []
        >>> # When folder is empty string, returns empty list
        >>> folder2notebooks("")
        []

    """
    if folder is None or folder == "":
        return []

    notebooks = list(Path(folder).glob("*.py"))
    notebooks.sort()

    return [Notebook(path=nb, kind=kind) for nb in notebooks]
