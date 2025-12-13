"""Notebook module for handling marimo notebooks.

This module provides the Notebook class for representing and exporting marimo notebooks.
"""

import dataclasses
import shutil
import subprocess
from enum import Enum
from pathlib import Path

from loguru import logger


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
            FileNotFoundError: If the file does not exist
            ValueError: If the path is not a file or not a Python file

        """
        if not self.path.exists():
            raise FileNotFoundError(f"File not found: {self.path}")
        if not self.path.is_file():
            raise ValueError(f"Path is not a file: {self.path}")
        if not self.path.suffix == ".py":
            raise ValueError(f"File is not a Python file: {self.path}")

    def export(self, output_dir: Path, sandbox: bool = True, bin_path: Path | None = None) -> bool:
        """Export the notebook to HTML/WebAssembly format.

        This method exports the marimo notebook to HTML/WebAssembly format.
        If is_app is True, the notebook is exported in "run" mode with code hidden,
        suitable for applications. Otherwise, it's exported in "edit" mode,
        suitable for interactive notebooks.

        Args:
            output_dir (Path): Directory where the exported HTML file will be saved
            sandbox (bool): Whether to run the notebook in a sandbox. Defaults to True.
            bin_path (Path | None): The directory where the executable is located. Defaults to None.

        Returns:
            bool: True if export succeeded, False otherwise

        """
        executable = "uvx"
        if bin_path:
            # Use shutil.which to find the executable in the specified directory
            # This handles platform-specific extensions (like .exe on Windows)
            exe = shutil.which(executable, path=str(bin_path))
            if not exe:
                logger.error(f"Could not find {executable} in {bin_path}")
                return False
        else:
            exe = executable

        cmd = [exe, *self.kind.command]
        if sandbox:
            cmd.append("--sandbox")
        else:
            cmd.append("--no-sandbox")

        try:
            # Create the full output path and ensure the directory exists
            output_file: Path = output_dir / f"{self.path.stem}.html"
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Add the notebook path and output file to command
            cmd.extend([str(self.path), "-o", str(output_file)])

            # Run marimo export command
            logger.debug(f"Running command: {cmd}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            nb_logger = logger.bind(subprocess=f"[{self.path.name}] ")

            if result.stdout:
                nb_logger.info(f"stdout:\n{result.stdout.strip()}")

            if result.stderr:
                nb_logger.warning(f"stderr:\n{result.stderr.strip()}")

            if result.returncode != 0:
                nb_logger.error(f"Error exporting {self.path}")
                return False

            return True
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error exporting {self.path}: {e}")
            return False

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

    # uvx marimo export html-wasm / html --sandbox (--mode edit/run) (
    return [Notebook(path=nb, kind=kind) for nb in notebooks]
