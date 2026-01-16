"""Notebook module for handling marimo notebooks.

This module provides the Notebook class for representing and exporting marimo notebooks.
"""

import dataclasses
import os
import shutil
import subprocess
from enum import Enum
from pathlib import Path

from loguru import logger

from .exceptions import (
    ExportExecutableNotFoundError,
    ExportSubprocessError,
    NotebookExportResult,
    NotebookInvalidError,
    NotebookNotFoundError,
)


class Kind(Enum):
    """Kind of notebook."""

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

        """
        try:
            return Kind(value)
        except ValueError as e:
            raise ValueError(f"Invalid Kind: {value!r}. Must be one of {[k.value for k in Kind]}") from e

    @property
    def command(self) -> list[str]:
        """Get the command list associated with a specific Kind instance.

        The command property returns a list of command strings that correspond
        to different kinds of operations based on the Kind instance.

        Attributes:
            command: A list of strings representing the command.

        Returns:
            list[str]: A list of command strings for the corresponding Kind instance.

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

    def __post_init__(self):
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

    def export(self, output_dir: Path, sandbox: bool = True, bin_path: Path | None = None) -> NotebookExportResult:
        """Export the notebook to HTML/WebAssembly format.

        This method exports the marimo notebook to HTML/WebAssembly format.
        If is_app is True, the notebook is exported in "run" mode with code hidden,
        suitable for applications. Otherwise, it's exported in "edit" mode,
        suitable for interactive notebooks.

        Args:
            output_dir: Directory where the exported HTML file will be saved.
            sandbox: Whether to run the notebook in a sandbox. Defaults to True.
            bin_path: The directory where the executable is located. Defaults to None.

        Returns:
            NotebookExportResult indicating success or failure with details.

        """
        executable = "uvx"
        exe: str | None = None

        if bin_path:
            # Construct the full executable path
            # Use shutil.which to find it with platform-specific extensions (like .exe on Windows)
            exe = shutil.which(executable, path=str(bin_path))
            if not exe:
                # Fallback: try constructing the path directly
                exe_path = bin_path / executable
                if exe_path.is_file() and os.access(exe_path, os.X_OK):
                    exe = str(exe_path)
                else:
                    error = ExportExecutableNotFoundError(executable, bin_path)
                    logger.error(str(error))
                    return NotebookExportResult.failed(self.path, error)
        else:
            exe = executable

        cmd = [exe, *self.kind.command]
        if sandbox:
            cmd.append("--sandbox")
        else:
            cmd.append("--no-sandbox")

        # Create the full output path and ensure the directory exists
        output_file: Path = output_dir / f"{self.path.stem}.html"

        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            error = ExportSubprocessError(
                notebook_path=self.path,
                command=cmd,
                return_code=-1,
                stderr=f"Failed to create output directory: {e}",
            )
            logger.error(str(error))
            return NotebookExportResult.failed(self.path, error)

        # Add the notebook path and output file to command
        cmd.extend([str(self.path), "-o", str(output_file)])

        try:
            # Run marimo export command
            logger.debug(f"Running command: {cmd}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            nb_logger = logger.bind(subprocess=f"[{self.path.name}] ")

            if result.stdout:
                nb_logger.info(f"stdout:\n{result.stdout.strip()}")

            if result.stderr:
                nb_logger.warning(f"stderr:\n{result.stderr.strip()}")

            if result.returncode != 0:
                error = ExportSubprocessError(
                    notebook_path=self.path,
                    command=cmd,
                    return_code=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )
                nb_logger.error(str(error))
                return NotebookExportResult.failed(self.path, error)

            return NotebookExportResult.succeeded(self.path, output_file)

        except FileNotFoundError as e:
            # Executable not found in PATH
            error = ExportExecutableNotFoundError(executable)
            logger.error(f"{error}: {e}")
            return NotebookExportResult.failed(self.path, error)
        except subprocess.SubprocessError as e:
            error = ExportSubprocessError(
                notebook_path=self.path,
                command=cmd,
                return_code=-1,
                stderr=str(e),
            )
            logger.error(str(error))
            return NotebookExportResult.failed(self.path, error)

    @property
    def display_name(self) -> str:
        """Return the display name for the notebook."""
        return self.path.stem.replace("_", " ")

    @property
    def html_path(self) -> Path:
        """Return the path to the exported HTML file."""
        return self.kind.html_path / f"{self.path.stem}.html"


def folder2notebooks(folder: Path | str | None, kind: Kind = Kind.NB) -> list[Notebook]:
    """Find all marimo notebooks in a directory."""
    if folder is None or folder == "":
        return []

    # which files are included here?
    notebooks = list(Path(folder).glob("*.py"))

    # Sort notebooks alphabetically by filename to ensure consistent ordering
    notebooks.sort()

    # uvx marimo export html-wasm / html --sandbox (--mode edit/run) (
    return [Notebook(path=nb, kind=kind) for nb in notebooks]
