"""Tests for the help command."""

import subprocess


def test_no_args(marimushka_path):
    """Test the help command."""
    # Run the command and capture the output
    result = subprocess.run([marimushka_path], capture_output=True, text=True, check=True)
    print("Command succeeded:")
    print(result.stdout)


def test_help(marimushka_path):
    """Test the help command."""
    # Run the command and capture the output
    result = subprocess.run([marimushka_path, "--help"], capture_output=True, text=True, check=True)
    print("Command succeeded:")
    print(result.stdout)


def test_export_help(marimushka_path):
    """Test the export command."""
    # Run the command and capture the output
    result = subprocess.run([marimushka_path, "export", "--help"], capture_output=True, text=True, check=True)
    print("Command succeeded:")
    print(result.stdout)
