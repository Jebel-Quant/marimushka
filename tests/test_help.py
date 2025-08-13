"""Tests for the help command."""

import subprocess


def test_no_args():
    """Test the help command."""
    # Run the command and capture the output
    result = subprocess.run(["marimushka"], capture_output=True, text=True, check=True)
    print("Command succeeded:")
    print(result.stdout)


def test_help():
    """Test the help command."""
    # Run the command and capture the output
    result = subprocess.run(["marimushka", "--help"], capture_output=True, text=True, check=True)
    print("Command succeeded:")
    print(result.stdout)


def test_export_help():
    """Test the export command."""
    # Run the command and capture the output
    result = subprocess.run(["marimushka", "export", "--help"], capture_output=True, text=True, check=True)
    print("Command succeeded:")
    print(result.stdout)
