"""Tests for the export.py module.

This module contains tests for the functions in the export.py module:
- _folder2notebooks
- _generate_index
- main
- cli
"""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import jinja2
import pytest
import typer

from marimushka.export import _generate_index, main
from marimushka.notebook import Kind, folder2notebooks


class TestFolder2Notebooks:
    """Tests for the _folder2notebooks function."""

    def test_folder2notebooks_none(self):
        """Test _folder2notebooks with None folder."""
        # Execute
        result = folder2notebooks(folder=None)

        # Assert
        assert result == []

    def test_folder2notebooks_empty_string(self):
        """Test _folder2notebooks with '' folder."""
        # Execute
        result = folder2notebooks(folder="")

        # Assert
        assert result == []

    def test_folder2notebooks_empty(self, tmp_path):
        """Test _folder2notebooks with empty folder."""
        # Setup
        empty_folder = tmp_path / "empty"
        empty_folder.mkdir()

        # Execute
        result = folder2notebooks(folder=empty_folder)

        # Assert
        assert result == []

    def test_folder2notebooks_with_notebooks(self, tmp_path):
        """Test _folder2notebooks with notebooks."""
        # Setup
        notebooks_folder = tmp_path / "notebooks"
        notebooks_folder.mkdir()

        # Create some test notebook files
        notebook1 = notebooks_folder / "notebook1.py"
        notebook2 = notebooks_folder / "notebook2.py"
        notebook1.write_text("# Test notebook 1")
        notebook2.write_text("# Test notebook 2")

        # Execute
        result = folder2notebooks(folder=notebooks_folder, kind=Kind.NB)

        # Assert
        assert len(result) == 2
        # assert all(not notebook.is_app for notebook in result)
        # Check that the paths are correct (convert to string for easier comparison)
        notebook_paths = [str(notebook.path) for notebook in result]
        assert str(notebook1) in notebook_paths
        assert str(notebook2) in notebook_paths


class TestGenerateIndex:
    """Tests for the _generate_index function."""

    @patch.object(Path, "open", new_callable=mock_open)
    @patch("jinja2.Environment")
    def test_generate_index_success(self, mock_env, mock_file_open, tmp_path):
        """Test the successful generation of index.html."""
        # Setup
        output_dir = tmp_path / "output"
        template_file = Path("template_dir/template.html.j2")

        # Create mock notebooks and apps
        mock_notebook1 = MagicMock()
        mock_notebook2 = MagicMock()
        mock_app1 = MagicMock()

        mock_notebook1_wasm = MagicMock()

        notebooks = [mock_notebook1, mock_notebook2]
        apps = [mock_app1]
        notebooks_wasm = [mock_notebook1_wasm]

        # Mock the template rendering
        mock_template = MagicMock()
        mock_env.return_value.get_template.return_value = mock_template
        mock_template.render.return_value = "<html>Rendered content</html>"

        # Execute
        result = _generate_index(
            output=output_dir,
            template_file=template_file,
            notebooks=notebooks,
            apps=apps,
            notebooks_wasm=notebooks_wasm,
        )

        # Assert
        # Check that to_wasm was called for each notebook and app
        mock_notebook1.export.assert_called_once_with(output_dir=output_dir / "notebooks", sandbox=True, bin_path=None)
        mock_notebook2.export.assert_called_once_with(output_dir=output_dir / "notebooks", sandbox=True, bin_path=None)
        mock_app1.export.assert_called_once_with(output_dir=output_dir / "apps", sandbox=True, bin_path=None)

        # Check that the template was rendered and written to file
        mock_env.assert_called_once()
        mock_env.return_value.get_template.assert_called_once_with(template_file.name)
        mock_template.render.assert_called_once_with(notebooks=notebooks, apps=apps, notebooks_wasm=notebooks_wasm)
        mock_file_open.assert_called_once_with(output_dir / "index.html", "w")
        mock_file_open().write.assert_called_once_with("<html>Rendered content</html>")

        # Check that the function returns the rendered HTML
        assert result == "<html>Rendered content</html>"

    @patch.object(Path, "open", side_effect=OSError("File error"))
    @patch("jinja2.Environment")
    def test_generate_index_file_error(self, mock_env, mock_file_open, tmp_path):
        """Test handling of file error during index generation."""
        # Setup
        output_dir = tmp_path / "output"
        template_file = Path("template_dir/template.html.j2")

        # Create mock notebooks
        mock_notebook = MagicMock()
        notebooks = [mock_notebook]
        apps = []

        # Mock the template rendering
        mock_template = MagicMock()
        mock_env.return_value.get_template.return_value = mock_template
        mock_template.render.return_value = "<html>Rendered content</html>"

        # Execute and Assert (should not raise an exception)
        result = _generate_index(output=output_dir, template_file=template_file, notebooks=notebooks, apps=apps)

        # Check that to_wasm was still called
        mock_notebook.export.assert_called_once_with(output_dir=output_dir / "notebooks", sandbox=True, bin_path=None)

        # Check that the function returns the rendered HTML even if there's a file error
        assert result == "<html>Rendered content</html>"

    @patch("jinja2.Environment")
    @patch.object(Path, "mkdir")
    def test_generate_index_template_error(self, mock_mkdir, mock_env, tmp_path):
        """Test handling of template error during index generation."""
        # Setup
        output_dir = tmp_path / "output"
        template_file = Path("template_dir/template.html.j2")

        # Create mock notebooks
        mock_notebook = MagicMock()
        notebooks = [mock_notebook]
        apps = []

        # Mock the template error
        mock_env.side_effect = jinja2.exceptions.TemplateError("Template error")

        # Execute and Assert (should not raise an exception)
        result = _generate_index(output=output_dir, template_file=template_file, notebooks=notebooks, apps=apps)

        # Check that to_wasm was still called
        mock_notebook.export.assert_called_once_with(output_dir=output_dir / "notebooks", sandbox=True, bin_path=None)

        # Check that the function returns an empty string when there's a template error
        assert result == ""


class TestMain:
    """Tests for the main function."""

    @patch("marimushka.export.folder2notebooks")
    @patch("marimushka.export._generate_index")
    def test_main_success(self, mock_generate_index, mock_folder2notebooks):
        """Test successful execution of the main function."""
        # Setup
        mock_notebooks = [MagicMock(), MagicMock()]
        mock_apps = [MagicMock()]
        mock_notebooks_wasm = [MagicMock()]
        mock_folder2notebooks.side_effect = [mock_notebooks, mock_apps, mock_notebooks_wasm]

        # Execute
        main()

        # Assert
        assert mock_folder2notebooks.call_count == 3
        mock_folder2notebooks.assert_any_call(folder="notebooks", kind=Kind.NB)
        mock_folder2notebooks.assert_any_call(folder="apps", kind=Kind.APP)
        mock_folder2notebooks.assert_any_call(folder="notebooks", kind=Kind.NB_WASM)
        mock_generate_index.assert_called_once()

    @patch("marimushka.export.folder2notebooks")
    @patch("marimushka.export._generate_index")
    def test_main_no_notebooks_or_apps(self, mock_generate_index, mock_folder2notebooks):
        """Test handling of no notebooks or apps found."""
        # Setup
        mock_folder2notebooks.return_value = []

        # Execute
        main()

        # Assert
        assert mock_folder2notebooks.call_count == 3
        mock_folder2notebooks.assert_any_call(folder="notebooks", kind=Kind.NB)
        mock_folder2notebooks.assert_any_call(folder="apps", kind=Kind.APP)
        mock_folder2notebooks.assert_any_call(folder="notebooks", kind=Kind.NB_WASM)
        mock_generate_index.assert_not_called()

    @patch("marimushka.export.folder2notebooks")
    @patch("marimushka.export._generate_index")
    def test_main_custom_paths(self, mock_generate_index, mock_folder2notebooks, tmp_path):
        """Test main function with custom paths."""
        # Setup
        mock_notebooks = [MagicMock(), MagicMock()]
        mock_apps = [MagicMock()]
        mock_notebooks_wasm = [MagicMock()]

        mock_folder2notebooks.side_effect = [mock_notebooks, mock_apps, mock_notebooks_wasm]

        custom_output = tmp_path / "custom_output"
        custom_template = tmp_path / "custom_template.html.j2"
        custom_notebooks = tmp_path / "custom_notebooks"
        custom_apps = tmp_path / "custom_apps"
        custom_notebooks_wasm = tmp_path / "custom_notebooks_wasm"

        # Execute
        main(
            output=custom_output,
            template=custom_template,
            notebooks=custom_notebooks,
            apps=custom_apps,
            notebooks_wasm=custom_notebooks_wasm,
        )

        # Assert
        mock_folder2notebooks.assert_any_call(folder=custom_notebooks, kind=Kind.NB)
        mock_folder2notebooks.assert_any_call(folder=custom_apps, kind=Kind.APP)
        mock_folder2notebooks.assert_any_call(folder=custom_notebooks_wasm, kind=Kind.NB_WASM)

        mock_generate_index.assert_called_once_with(
            output=custom_output,
            template_file=custom_template,
            notebooks=mock_notebooks,
            apps=mock_apps,
            notebooks_wasm=mock_notebooks_wasm,
            sandbox=True,
            bin_path=None,
        )


class TestCallback:
    """Tests for the callback function."""

    @patch("builtins.print")
    def test_callback_without_command(self, mock_print):
        """Test callback function when no command is provided."""
        from marimushka.export import callback

        # Setup - create a mock context with no subcommand
        mock_ctx = MagicMock(spec=typer.Context)
        mock_ctx.invoked_subcommand = None
        mock_ctx.get_help.return_value = "Help text"

        # Execute and Assert - should raise typer.Exit
        with pytest.raises(typer.Exit):
            callback(mock_ctx)

        # Verify that help was printed
        mock_print.assert_called_once_with("Help text")
        mock_ctx.get_help.assert_called_once()

    def test_callback_with_command(self):
        """Test callback function when a command is provided."""
        from marimushka.export import callback

        # Setup - create a mock context with a subcommand
        mock_ctx = MagicMock(spec=typer.Context)
        mock_ctx.invoked_subcommand = "export"

        # Execute - should not raise any exception
        callback(mock_ctx)

        # Verify that help was not requested
        mock_ctx.get_help.assert_not_called()


class TestMainTyper:
    """Tests for the _main_typer function."""

    @patch("marimushka.export.main")
    def test_main_typer_with_option_objects(self, mock_main):
        """Test _main_typer function with typer.Option objects."""
        from marimushka.export import _main_typer

        # Setup - create mock Option objects with default attributes
        mock_output = MagicMock()
        mock_output.default = "custom_site"

        mock_template = MagicMock()
        mock_template.default = "custom_template.html"

        mock_notebooks = MagicMock()
        mock_notebooks.default = "custom_notebooks"

        mock_apps = MagicMock()
        mock_apps.default = "custom_apps"

        mock_notebooks_wasm = MagicMock()
        mock_notebooks_wasm.default = "custom_notebooks_wasm"

        mock_sandbox = MagicMock()
        mock_sandbox.default = False

        mock_bin_path = MagicMock()
        mock_bin_path.default = "/custom/bin"

        # Execute
        _main_typer(
            output=mock_output,
            template=mock_template,
            notebooks=mock_notebooks,
            apps=mock_apps,
            notebooks_wasm=mock_notebooks_wasm,
            sandbox=mock_sandbox,
            bin_path=mock_bin_path,
        )

        # Assert - verify that main was called with the default values
        mock_main.assert_called_once_with(
            output="custom_site",
            template="custom_template.html",
            notebooks="custom_notebooks",
            apps="custom_apps",
            notebooks_wasm="custom_notebooks_wasm",
            sandbox=False,
            bin_path="/custom/bin",
        )

    @patch("marimushka.export.main")
    def test_main_typer_with_string_values(self, mock_main):
        """Test _main_typer function with string values (not Option objects)."""
        from marimushka.export import _main_typer

        # Execute with regular string values
        _main_typer(
            output="output_dir",
            template="template.html",
            notebooks="notebooks",
            apps="apps",
            notebooks_wasm="notebooks_wasm",
            sandbox=True,
            bin_path="/bin",
        )

        # Assert - verify that main was called with the same values
        mock_main.assert_called_once_with(
            output="output_dir",
            template="template.html",
            notebooks="notebooks",
            apps="apps",
            notebooks_wasm="notebooks_wasm",
            sandbox=True,
            bin_path="/bin",
        )
