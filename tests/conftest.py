"""Pytest configuration file.

This file contains fixtures and configuration for pytest.
"""

import shutil
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from hypothesis import HealthCheck, Phase, settings

from marimushka.notebook import Kind, Notebook

# Hypothesis configuration for faster tests on Python 3.14+
# Python 3.14 has some performance regressions that affect hypothesis
if sys.version_info >= (3, 14):
    # Use a faster profile for Python 3.14+
    settings.register_profile(
        "py314",
        max_examples=20,  # Reduce from default 100
        deadline=2000,  # 2 seconds per example (increased from default)
        suppress_health_check=[HealthCheck.too_slow],
        phases=[Phase.generate, Phase.target],  # Skip shrinking phase
    )
    settings.load_profile("py314")
else:
    # Standard profile for Python 3.11-3.13
    settings.register_profile(
        "default",
        max_examples=50,  # Reasonable default
        deadline=1000,  # 1 second per example
    )
    settings.load_profile("default")


@pytest.fixture
def mock_logger():
    """Return a mock logger instance.

    Returns:
        MagicMock: A mock logger for testing.

    """
    return MagicMock()


@pytest.fixture
def resource_dir():
    """Pytest fixture that provides the path to the test resources directory.

    Returns:
        Path: A Path object pointing to the resources directory within the tests folder.

    """
    return Path(__file__).parent / "resources"


@pytest.fixture
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


# New fixtures for comprehensive testing


@pytest.fixture
def sample_notebook(tmp_path):
    """Create a sample notebook file for testing.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Notebook: A sample notebook instance.

    """
    notebook_path = tmp_path / "sample_notebook.py"
    notebook_path.write_text("# Sample marimo notebook\nimport marimo as mo\n")
    return Notebook(path=notebook_path, kind=Kind.NB)


@pytest.fixture
def sample_app(tmp_path):
    """Create a sample app file for testing.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Notebook: A sample app instance.

    """
    app_path = tmp_path / "sample_app.py"
    app_path.write_text("# Sample marimo app\nimport marimo as mo\n")
    return Notebook(path=app_path, kind=Kind.APP)


@pytest.fixture
def sample_notebook_wasm(tmp_path):
    """Create a sample interactive notebook file for testing.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Notebook: A sample interactive notebook instance.

    """
    notebook_path = tmp_path / "sample_notebook_wasm.py"
    notebook_path.write_text("# Sample interactive marimo notebook\nimport marimo as mo\n")
    return Notebook(path=notebook_path, kind=Kind.NB_WASM)


@pytest.fixture
def sample_template(tmp_path):
    """Create a sample Jinja2 template for testing.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Path: Path to the sample template file.

    """
    template_path = tmp_path / "sample_template.html.j2"
    template_path.write_text("""
<!DOCTYPE html>
<html>
<head><title>Test Template</title></head>
<body>
    <h1>Notebooks</h1>
    <ul>
    {% for nb in notebooks %}
        <li><a href="{{ nb.html_path }}">{{ nb.display_name }}</a></li>
    {% endfor %}
    </ul>
    <h1>Apps</h1>
    <ul>
    {% for app in apps %}
        <li><a href="{{ app.html_path }}">{{ app.display_name }}</a></li>
    {% endfor %}
    </ul>
</body>
</html>
""")
    return template_path


@pytest.fixture
def notebooks_dir(tmp_path):
    """Create a directory with sample notebooks for testing.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Path: Path to the notebooks directory.

    """
    nb_dir = tmp_path / "notebooks"
    nb_dir.mkdir()

    # Create a few sample notebooks
    (nb_dir / "notebook1.py").write_text("# Notebook 1\nimport marimo as mo\n")
    (nb_dir / "notebook2.py").write_text("# Notebook 2\nimport marimo as mo\n")
    (nb_dir / "notebook3.py").write_text("# Notebook 3\nimport marimo as mo\n")

    return nb_dir


@pytest.fixture
def apps_dir(tmp_path):
    """Create a directory with sample apps for testing.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Path: Path to the apps directory.

    """
    app_dir = tmp_path / "apps"
    app_dir.mkdir()

    # Create a few sample apps
    (app_dir / "app1.py").write_text("# App 1\nimport marimo as mo\n")
    (app_dir / "app2.py").write_text("# App 2\nimport marimo as mo\n")

    return app_dir


@pytest.fixture
def output_dir(tmp_path):
    """Create an output directory for testing.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Path: Path to the output directory.

    """
    out_dir = tmp_path / "_site"
    out_dir.mkdir()
    return out_dir


@pytest.fixture(scope="session")
def progress_tracker():
    """Create a progress tracker for testing progress callbacks.

    Returns:
        list: A list to store progress reports.

    """
    return []


@pytest.fixture
def mock_audit_logger():
    """Create a mock audit logger for testing.

    Returns:
        MagicMock: A mock audit logger.

    """
    logger = MagicMock()
    logger.log_file_access = MagicMock()
    logger.log_template_render = MagicMock()
    return logger
