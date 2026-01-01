"""Tests for the notebook.py module.

This module contains tests for the Notebook class and Kind enum in the notebook.py module.
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from marimushka.notebook import Kind, Notebook


class TestKind:
    """Tests for the Kind enum."""

    def test_from_string(self):
        """Test cases for validating the Kind.from_str method.

        Tests the conversion of string representations to the corresponding Kind
        enum values. Ensures that valid string mappings return the expected enum
        value. Also ensures that invalid strings raise the appropriate exception.

        Raises:
            ValueError: If the input string does not correspond to any Kind enum.

        """
        kind = Kind.from_str("notebook")
        assert kind == Kind.NB

        kind = Kind.from_str("notebook_wasm")
        assert kind == Kind.NB_WASM

        kind = Kind.from_str("app")
        assert kind == Kind.APP

        with pytest.raises(ValueError):
            Kind.from_str("invalid_kind")

    def test_html_path(self):
        """Test the html_path property of the Kind enum."""
        # Test all three enum values
        assert Kind.NB.html_path == Path("notebooks")
        assert Kind.NB_WASM.html_path == Path("notebooks_wasm")
        assert Kind.APP.html_path == Path("apps")

    def test_command(self):
        """Test the command method of the Kind enum."""
        # Test all three enum values
        assert Kind.NB.command == ["marimo", "export", "html"]
        assert Kind.NB_WASM.command == ["marimo", "export", "html-wasm", "--mode", "edit"]
        assert Kind.APP.command == [
            "marimo",
            "export",
            "html-wasm",
            "--mode",
            "run",
            "--no-show-code",
        ]


class TestNotebook:
    """Tests for the Notebook class."""

    def test_init_success(self, resource_dir):
        """Test successful initialization of a Notebook."""
        # Setup
        notebook_path = resource_dir / "notebooks" / "fibonacci.py"

        # Create a mock path that exists and is a Python file
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "suffix", ".py"),
        ):
            # Execute
            notebook = Notebook(notebook_path)

            # Assert
            assert notebook.path == notebook_path

    def test_init_with_app(self, resource_dir):
        """Test initialization of a Notebook as an app."""
        # Setup
        notebook_path = resource_dir / "apps" / "charts.py"

        # Create a mock path that exists and is a Python file
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "suffix", ".py"),
        ):
            # Execute
            notebook = Notebook(notebook_path, kind=Kind.APP)

            # Assert
            assert notebook.path == notebook_path
            assert notebook.kind == Kind.APP

    def test_init_file_not_found(self):
        """Test initialization with a non-existent file."""
        # Setup
        notebook_path = Path("nonexistent_file.py")

        # Mock Path.exists to return False and execute/assert
        with patch.object(Path, "exists", return_value=False), pytest.raises(FileNotFoundError):
            Notebook(notebook_path)

    def test_init_not_a_file(self):
        """Test initialization with a path that is not a file."""
        # Setup
        notebook_path = Path("directory")

        # Mock Path.exists to return True and Path.is_file to return False, then execute/assert
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=False),
            pytest.raises(ValueError),
        ):
            Notebook(notebook_path)

    def test_init_not_python_file(self):
        """Test initialization with a non-Python file."""
        # Setup
        notebook_path = Path("file.txt")

        # Mock Path.exists and Path.is_file to return True, but set suffix to .txt, then execute/assert
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "suffix", ".txt"),
            pytest.raises(ValueError),
        ):
            Notebook(notebook_path)

    @patch("subprocess.run")
    def test_to_wasm_success(self, mock_run, resource_dir, tmp_path):
        """Test successful export of a notebook to WebAssembly."""
        # Setup
        notebook_path = resource_dir / "notebooks" / "fibonacci.py"
        output_dir = tmp_path

        # Mock successful subprocess run
        mock_run.return_value = MagicMock(returncode=0)

        # Create a notebook with mocked path validation
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "suffix", ".py"),
        ):
            notebook = Notebook(notebook_path, kind=Kind.NB)  # Changed to Kind.NB

            # Execute
            result = notebook.export(output_dir)

            # Assert
            assert result is True
            mock_run.assert_called_once()

            # Check that the command includes the notebook-specific flags
            cmd_args = mock_run.call_args[0][0]
            print(cmd_args)
            assert "--sandbox" in cmd_args
            assert "--no-show-code" not in cmd_args

    @patch("subprocess.run")
    def test_to_wasm_as_app(self, mock_run, resource_dir, tmp_path):
        """Test export of a notebook as an app."""
        # Setup
        notebook_path = resource_dir / "apps" / "charts.py"
        output_dir = tmp_path

        # Mock successful subprocess run
        mock_run.return_value = MagicMock(returncode=0)

        # Create a notebook with mocked path validation
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "suffix", ".py"),
        ):
            notebook = Notebook(notebook_path, kind=Kind.APP)

            # Execute
            result = notebook.export(output_dir)

            # Assert
            assert result is True
            mock_run.assert_called_once()

            # Check that the command includes the app-specific flags
            cmd_args = mock_run.call_args[0][0]
            assert "--mode" in cmd_args
            assert "run" in cmd_args
            assert "--no-show-code" in cmd_args

    @patch("subprocess.run")
    def test_to_wasm_subprocess_error(self, mock_run, resource_dir, tmp_path):
        """Test handling of subprocess error during export."""
        # Setup
        notebook_path = resource_dir / "notebooks" / "fibonacci.py"
        output_dir = tmp_path

        # Mock subprocess error
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="Error message")

        # Create a notebook with mocked path validation
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "suffix", ".py"),
        ):
            notebook = Notebook(notebook_path)

            # Execute
            result = notebook.export(output_dir)

            # Assert
            assert result is False

    @patch("subprocess.run")
    def test_to_wasm_general_exception(self, mock_run, resource_dir, tmp_path):
        """Test handling of general exception during export."""
        # Setup
        notebook_path = resource_dir / "notebooks" / "fibonacci.py"
        output_dir = tmp_path

        # Mock general exception
        mock_run.side_effect = Exception("Unexpected error")

        # Create a notebook with mocked path validation
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "suffix", ".py"),
        ):
            notebook = Notebook(notebook_path)

            # Execute
            result = notebook.export(output_dir)

            # Assert
            assert result is False

    @patch("subprocess.run")
    def test_export_no_sandbox(self, mock_run, resource_dir, tmp_path):
        """Test export of a notebook without sandbox."""
        # Setup
        notebook_path = resource_dir / "notebooks" / "fibonacci.py"
        output_dir = tmp_path

        # Mock successful subprocess run
        mock_run.return_value = MagicMock(returncode=0)

        # Create a notebook with mocked path validation
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "suffix", ".py"),
        ):
            notebook = Notebook(notebook_path, kind=Kind.NB)

            # Execute
            result = notebook.export(output_dir, sandbox=False)

            # Assert
            assert result is True
            mock_run.assert_called_once()

            # Check that the command does NOT include --sandbox
            cmd_args = mock_run.call_args[0][0]
            assert "--sandbox" not in cmd_args

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_export_bin_path(self, mock_run, mock_which, resource_dir, tmp_path):
        """Test export of a notebook with a bin path."""
        # Setup
        notebook_path = resource_dir / "notebooks" / "fibonacci.py"
        output_dir = tmp_path
        bin_path = Path("/custom/bin")
        executable = "uvx"

        # Mock successful subprocess run
        mock_run.return_value = MagicMock(returncode=0)
        # Mock shutil.which to return the path
        mock_which.return_value = str(bin_path / executable)

        # Create a notebook with mocked path validation
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "suffix", ".py"),
        ):
            notebook = Notebook(notebook_path, kind=Kind.NB)

            # Execute
            result = notebook.export(output_dir, bin_path=bin_path)

            # Assert
            assert result is True
            mock_run.assert_called_once()

            # Check that the command starts with the combined path
            cmd_args = mock_run.call_args[0][0]
            # shutil.which returns the full path, so we check if it ends with the executable name
            assert cmd_args[0].endswith(executable)

    @patch("os.access")
    @patch("shutil.which")
    @patch("subprocess.run")
    def test_export_bin_path_fallback_success(self, mock_run, mock_which, mock_access, resource_dir, tmp_path):
        """Test export of a notebook with fallback when shutil.which fails."""
        # Setup
        notebook_path = resource_dir / "notebooks" / "fibonacci.py"
        output_dir = tmp_path
        bin_path = Path("/custom/bin")
        executable = "uvx"

        # Mock shutil.which to return None (simulating the case where it doesn't work)
        mock_which.return_value = None
        # Mock os.access to return True (executable is accessible)
        mock_access.return_value = True
        # Mock successful subprocess run
        mock_run.return_value = MagicMock(returncode=0)

        # Create a notebook with mocked path validation
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "suffix", ".py"),
        ):
            notebook = Notebook(notebook_path, kind=Kind.NB)

            # Mock the is_file check on the executable path
            with patch.object(Path, "is_file", return_value=True):
                # Execute
                result = notebook.export(output_dir, bin_path=bin_path)

                # Assert
                assert result is True
                mock_run.assert_called_once()

                # Check that the command uses the fallback path
                cmd_args = mock_run.call_args[0][0]
                assert cmd_args[0] == str(bin_path / executable)

    @patch("os.access")
    @patch("shutil.which")
    def test_export_bin_path_not_found(self, mock_which, mock_access, resource_dir, tmp_path):
        """Test export of a notebook when bin path executable is not found."""
        # Setup
        notebook_path = resource_dir / "notebooks" / "fibonacci.py"
        output_dir = tmp_path
        bin_path = Path("/invalid/bin")

        # Mock shutil.which to return None
        mock_which.return_value = None
        # Mock os.access to return False (executable is not accessible)
        mock_access.return_value = False

        # Create a notebook with mocked path validation
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "suffix", ".py"),
        ):
            notebook = Notebook(notebook_path, kind=Kind.NB)

            # Mock the is_file check on the executable path to return False
            with patch.object(Path, "is_file", return_value=False):
                # Execute
                result = notebook.export(output_dir, bin_path=bin_path)

                # Assert
                assert result is False

    @patch("subprocess.run")
    def test_export_nonzero_returncode(self, mock_run, resource_dir, tmp_path):
        """Test export of a notebook when subprocess returns non-zero exit code."""
        # Setup
        notebook_path = resource_dir / "notebooks" / "fibonacci.py"
        output_dir = tmp_path

        # Mock subprocess run with non-zero returncode
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Export failed")

        # Create a notebook with mocked path validation
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "suffix", ".py"),
        ):
            notebook = Notebook(notebook_path, kind=Kind.NB)

            # Execute
            result = notebook.export(output_dir)

            # Assert
            assert result is False
            mock_run.assert_called_once()

    def test_display_name(self, resource_dir):
        """Test the display_name property of the Notebook class."""
        # Setup
        notebook_path = resource_dir / "notebooks" / "fibonacci.py"

        # Create a notebook with mocked path validation
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "suffix", ".py"),
        ):
            notebook = Notebook(notebook_path, kind=Kind.NB)

            # Execute
            display_name = notebook.display_name

            # Assert
            assert display_name == "fibonacci"

    def test_display_name_with_underscores(self):
        """Test the display_name property with underscores in the filename."""
        # Setup
        notebook_path = Path("my_test_notebook.py")

        # Create a notebook with mocked path validation
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "suffix", ".py"),
        ):
            notebook = Notebook(notebook_path, kind=Kind.NB)

            # Execute
            display_name = notebook.display_name

            # Assert
            assert display_name == "my test notebook"

    def test_html_path(self, resource_dir):
        """Test the html_path property of the Notebook class."""
        # Setup
        notebook_path = resource_dir / "notebooks" / "fibonacci.py"

        # Create a notebook with mocked path validation
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "suffix", ".py"),
        ):
            notebook = Notebook(notebook_path, kind=Kind.NB)

            # Execute
            html_path = notebook.html_path

            # Assert
            assert html_path == Path("notebooks") / "fibonacci.html"

    def test_html_path_app(self, resource_dir):
        """Test the html_path property for an app notebook."""
        # Setup
        notebook_path = resource_dir / "apps" / "charts.py"

        # Create a notebook with mocked path validation
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "suffix", ".py"),
        ):
            notebook = Notebook(notebook_path, kind=Kind.APP)

            # Execute
            html_path = notebook.html_path

            # Assert
            assert html_path == Path("apps") / "charts.html"
