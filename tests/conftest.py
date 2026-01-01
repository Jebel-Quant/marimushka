"""Pytest configuration file.

This file contains fixtures and configuration for pytest.
"""

import shutil
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_logger():
    """Return a mock logger instance."""
    return MagicMock()


@pytest.fixture()
def resource_dir():
    """Pytest fixture that provides the path to the test resources directory.

    Returns:
        Path: A Path object pointing to the resources directory within the tests folder.

    """
    return Path(__file__).parent / "resources"


@pytest.fixture()
def marimushka_path():
    """Pytest fixture that provides the path to the marimushka executable.

    This fixture finds the marimushka executable, looking in multiple locations:
    1. In PATH (via shutil.which)
    2. In the same directory as the Python interpreter (for virtual environments)
    3. In the user's local bin directory (~/.local/bin)

    Returns:
        str: The full path to the marimushka executable.

    Raises:
        RuntimeError: If the marimushka executable cannot be found.

    """
    # First, try to find it in PATH
    marimushka_exe = shutil.which("marimushka")
    if marimushka_exe:
        return marimushka_exe

    # If not in PATH, check in the same directory as the Python interpreter
    # This handles the case where we're running in a virtual environment
    python_dir = Path(sys.executable).parent
    venv_marimushka = python_dir / "marimushka"
    if venv_marimushka.exists() and venv_marimushka.is_file():
        return str(venv_marimushka)

    # Also check for .exe extension (Windows)
    venv_marimushka_exe = python_dir / "marimushka.exe"
    if venv_marimushka_exe.exists() and venv_marimushka_exe.is_file():
        return str(venv_marimushka_exe)

    # Check in user's local bin directory
    local_bin = Path.home() / ".local" / "bin" / "marimushka"
    if local_bin.exists() and local_bin.is_file():
        return str(local_bin)

    # If we still can't find it, raise an error
    msg = "marimushka executable not found in PATH or virtual environment"
    raise RuntimeError(msg)
