"""Tests for the notebook.py module.

This module contains tests for the Notebook class and Kind enum in the notebook.py module.
"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given
from hypothesis import strategies as st

from marimushka.exceptions import (
    ExportExecutableNotFoundError,
    ExportSubprocessError,
    NotebookInvalidError,
    NotebookNotFoundError,
)
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

        with pytest.raises(ValueError, match="Invalid Kind"):
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
        with patch.object(Path, "exists", return_value=False), pytest.raises(NotebookNotFoundError) as exc_info:
            Notebook(notebook_path)
        assert exc_info.value.notebook_path == notebook_path

    def test_init_not_a_file(self):
        """Test initialization with a path that is not a file."""
        # Setup
        notebook_path = Path("directory")

        # Mock Path.exists to return True and Path.is_file to return False, then execute/assert
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=False),
            pytest.raises(NotebookInvalidError) as exc_info,
        ):
            Notebook(notebook_path)
        assert exc_info.value.notebook_path == notebook_path
        assert "not a file" in exc_info.value.reason

    def test_init_not_python_file(self):
        """Test initialization with a non-Python file."""
        # Setup
        notebook_path = Path("file.txt")

        # Mock Path.exists and Path.is_file to return True, but set suffix to .txt, then execute/assert
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "suffix", ".txt"),
            pytest.raises(NotebookInvalidError) as exc_info,
        ):
            Notebook(notebook_path)
        assert "Python file" in exc_info.value.reason

    @patch("subprocess.run")
    def test_to_wasm_success(self, mock_run, resource_dir, tmp_path):
        """Test successful export of a notebook to WebAssembly."""
        # Setup
        notebook_path = resource_dir / "notebooks" / "fibonacci.py"
        output_dir = tmp_path

        # Mock successful subprocess run
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

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
            assert result.success is True
            assert result.notebook_path == notebook_path
            assert result.output_path is not None
            assert result.error is None
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
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

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
            assert result.success is True
            assert result.notebook_path == notebook_path
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
            assert result.success is False
            assert result.error is not None
            assert isinstance(result.error, ExportSubprocessError)

    @patch("subprocess.run")
    def test_to_wasm_file_not_found_error(self, mock_run, resource_dir, tmp_path):
        """Test handling of FileNotFoundError (executable not found) during export."""
        # Setup
        notebook_path = resource_dir / "notebooks" / "fibonacci.py"
        output_dir = tmp_path

        # Mock FileNotFoundError (executable not in PATH)
        mock_run.side_effect = FileNotFoundError("uvx not found")

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
            assert result.success is False
            assert result.error is not None
            assert isinstance(result.error, ExportExecutableNotFoundError)

    @patch("subprocess.run")
    def test_export_no_sandbox(self, mock_run, resource_dir, tmp_path):
        """Test export of a notebook without sandbox."""
        # Setup
        notebook_path = resource_dir / "notebooks" / "fibonacci.py"
        output_dir = tmp_path

        # Mock successful subprocess run
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

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
            assert result.success is True
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
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
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
            assert result.success is True
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
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

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
                assert result.success is True
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
                assert result.success is False
                assert result.error is not None
                assert isinstance(result.error, ExportExecutableNotFoundError)
                assert result.error.search_path == bin_path

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
            assert result.success is False
            assert result.error is not None
            assert isinstance(result.error, ExportSubprocessError)
            assert result.error.return_code == 1
            assert result.error.stderr == "Export failed"
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


class TestKindHypothesis:
    """Property-based tests for the Kind enum using hypothesis."""

    @given(kind=st.sampled_from(list(Kind)))
    def test_from_str_roundtrip(self, kind: Kind):
        """Test that Kind.from_str correctly round-trips all valid Kind values."""
        result = Kind.from_str(kind.value)
        assert result == kind

    @given(invalid_value=st.text().filter(lambda x: x not in [k.value for k in Kind]))
    def test_from_str_rejects_invalid(self, invalid_value: str):
        """Test that Kind.from_str raises ValueError for any invalid string."""
        with pytest.raises(ValueError, match="Invalid Kind") as exc_info:
            Kind.from_str(invalid_value)
        # Use repr() since special characters may be escaped in error message
        assert repr(invalid_value) in str(exc_info.value)

    @given(kind=st.sampled_from(list(Kind)))
    def test_command_returns_list_starting_with_marimo(self, kind: Kind):
        """Test that command property always returns a list starting with 'marimo'."""
        cmd = kind.command
        assert isinstance(cmd, list)
        assert len(cmd) >= 3
        assert cmd[0] == "marimo"
        assert cmd[1] == "export"

    @given(kind=st.sampled_from(list(Kind)))
    def test_html_path_returns_path(self, kind: Kind):
        """Test that html_path property always returns a valid Path."""
        path = kind.html_path
        assert isinstance(path, Path)
        assert not path.is_absolute()


class TestNotebookHypothesis:
    """Property-based tests for the Notebook class using hypothesis."""

    @given(
        stem=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_-"),
            min_size=1,
            max_size=50,
        ).filter(lambda x: x.strip() and not x.startswith("-"))
    )
    def test_display_name_replaces_underscores(self, stem: str):
        """Test that display_name replaces all underscores with spaces."""
        notebook_path = Path(f"{stem}.py")

        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "suffix", ".py"),
        ):
            notebook = Notebook(notebook_path)
            display_name = notebook.display_name

            assert "_" not in display_name
            assert display_name == stem.replace("_", " ")

    @given(
        stem=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_-"),
            min_size=1,
            max_size=50,
        ).filter(lambda x: x.strip() and not x.startswith("-")),
        kind=st.sampled_from(list(Kind)),
    )
    def test_html_path_structure(self, stem: str, kind: Kind):
        """Test that html_path correctly combines kind's html_path with notebook stem."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            notebook_path = Path(tmp_dir) / f"{stem}.py"
            notebook_path.touch()

            notebook = Notebook(notebook_path, kind=kind)
            html_path = notebook.html_path

            assert html_path.suffix == ".html"
            assert html_path.stem == stem
            assert html_path.parent == kind.html_path


class TestFolder2NotebooksHypothesis:
    """Property-based tests for folder2notebooks function using hypothesis."""

    @given(kind=st.sampled_from(list(Kind)))
    def test_empty_folder_returns_empty_list(self, kind: Kind):
        """Test that None or empty string folder returns empty list for any Kind."""
        from marimushka.notebook import folder2notebooks

        assert folder2notebooks(None, kind=kind) == []
        assert folder2notebooks("", kind=kind) == []

    @given(kind=st.sampled_from(list(Kind)))
    def test_notebooks_have_correct_kind(self, kind: Kind):
        """Test that all notebooks from folder2notebooks have the specified kind."""
        from marimushka.notebook import folder2notebooks

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            # Create some test files
            (tmp_path / "test1.py").touch()
            (tmp_path / "test2.py").touch()
            (tmp_path / "not_a_notebook.txt").touch()

            notebooks = folder2notebooks(tmp_path, kind=kind)

            assert len(notebooks) == 2
            for nb in notebooks:
                assert nb.kind == kind

    @given(kind=st.sampled_from(list(Kind)))
    def test_notebooks_are_sorted(self, kind: Kind):
        """Test that notebooks from folder2notebooks are sorted alphabetically."""
        from marimushka.notebook import folder2notebooks

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            # Create files in non-alphabetical order
            (tmp_path / "zebra.py").touch()
            (tmp_path / "alpha.py").touch()
            (tmp_path / "middle.py").touch()

            notebooks = folder2notebooks(tmp_path, kind=kind)

            names = [nb.path.name for nb in notebooks]
            assert names == sorted(names)
