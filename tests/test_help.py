"""Tests for the help command."""

import shutil
import subprocess


def test_no_args():
    """Test the help command."""
    # Resolve the full path to the marimushka executable
    marimushka_path = shutil.which("marimushka")
    if not marimushka_path:
        raise RuntimeError("marimushka executable not found in PATH")
    
    # Run the command and capture the output
    result = subprocess.run([marimushka_path], capture_output=True, text=True, check=True)
    print("Command succeeded:")
    print(result.stdout)


def test_help():
    """Test the help command."""
    # Resolve the full path to the marimushka executable
    marimushka_path = shutil.which("marimushka")
    if not marimushka_path:
        raise RuntimeError("marimushka executable not found in PATH")
    
    # Run the command and capture the output
    result = subprocess.run([marimushka_path, "--help"], capture_output=True, text=True, check=True)
    print("Command succeeded:")
    print(result.stdout)


def test_export_help():
    """Test the export command."""
    # Resolve the full path to the marimushka executable
    marimushka_path = shutil.which("marimushka")
    if not marimushka_path:
        raise RuntimeError("marimushka executable not found in PATH")
    
    # Run the command and capture the output
    result = subprocess.run([marimushka_path, "export", "--help"], capture_output=True, text=True, check=True)
    print("Command succeeded:")
    print(result.stdout)
