"""Tests for the command line interface."""

import subprocess
from unittest.mock import patch

from marimushka.export import cli, version


@patch("marimushka.export.app")
def test_cli(mock_app):
    """Test the cli function."""
    # Execute
    cli()

    # Assert
    mock_app.assert_called_once()


@patch("marimushka.export.rich_print")
def test_version(mock_rich_print):
    """Test the version command."""
    # Execute
    version()

    # Assert
    mock_rich_print.assert_called_once()


def test_export_run(marimushka_path):
    """Test the export command."""
    # Run the command and capture the output
    result = subprocess.run([marimushka_path, "export"], capture_output=True, text=True, check=True)
    print("Command succeeded:")
    print(result.stdout)
