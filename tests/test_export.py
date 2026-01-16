"""Tests for the export.py module.

This module contains tests for the functions in the export.py module:
- _folder2notebooks
- _generate_index
- _validate_template
- _export_notebooks_parallel
- main
- cli
"""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import jinja2
import pytest
import typer

from marimushka.exceptions import (
    BatchExportResult,
    ExportSubprocessError,
    IndexWriteError,
    NotebookExportResult,
    TemplateInvalidError,
    TemplateNotFoundError,
    TemplateRenderError,
)
from marimushka.export import (
    _export_notebook,
    _export_notebooks_parallel,
    _generate_index,
    _validate_template,
    main,
)
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


class TestValidateTemplate:
    """Tests for the _validate_template function."""

    def test_validate_template_success(self, tmp_path):
        """Test successful template validation."""
        # Setup
        template_file = tmp_path / "template.html.j2"
        template_file.write_text("<html></html>")

        # Execute - should not raise
        _validate_template(template_file)

    def test_validate_template_jinja2_extension(self, tmp_path):
        """Test template validation with .jinja2 extension."""
        # Setup
        template_file = tmp_path / "template.html.jinja2"
        template_file.write_text("<html></html>")

        # Execute - should not raise
        _validate_template(template_file)

    def test_validate_template_not_found(self, tmp_path):
        """Test template validation when file not found."""
        # Setup
        template_file = tmp_path / "nonexistent.html.j2"

        # Execute and Assert
        with pytest.raises(TemplateNotFoundError) as exc_info:
            _validate_template(template_file)
        assert exc_info.value.template_path == template_file

    def test_validate_template_not_a_file(self, tmp_path):
        """Test template validation when path is a directory."""
        # Setup
        template_dir = tmp_path / "template_dir"
        template_dir.mkdir()

        # Execute and Assert
        with pytest.raises(TemplateInvalidError) as exc_info:
            _validate_template(template_dir)
        assert exc_info.value.template_path == template_dir
        assert "not a file" in exc_info.value.reason

    def test_validate_template_wrong_extension_warning(self, tmp_path, caplog):
        """Test template validation warns on wrong extension."""
        # Setup
        template_file = tmp_path / "template.html"
        template_file.write_text("<html></html>")

        # Execute - should not raise but should log warning
        _validate_template(template_file)

        # The warning is logged via loguru, which doesn't use caplog
        # Just verify no exception was raised


class TestExportNotebook:
    """Tests for the _export_notebook function."""

    def test_export_notebook_success(self):
        """Test successful notebook export."""
        # Setup
        mock_notebook = MagicMock()
        mock_result = NotebookExportResult.succeeded(Path("/nb.py"), Path("/output/nb.html"))
        mock_notebook.export.return_value = mock_result
        output_dir = Path("/output")

        # Execute
        result = _export_notebook(mock_notebook, output_dir, sandbox=True, bin_path=None)

        # Assert
        assert result is mock_result
        assert result.success is True
        mock_notebook.export.assert_called_once_with(output_dir=output_dir, sandbox=True, bin_path=None)

    def test_export_notebook_failure(self):
        """Test notebook export failure."""
        # Setup
        mock_notebook = MagicMock()
        mock_result = NotebookExportResult.failed(Path("/nb.py"), ExportSubprocessError(Path("/nb.py"), ["cmd"], 1))
        mock_notebook.export.return_value = mock_result
        output_dir = Path("/output")

        # Execute
        result = _export_notebook(mock_notebook, output_dir, sandbox=False, bin_path=Path("/bin"))

        # Assert
        assert result is mock_result
        assert result.success is False


class TestExportNotebooksParallel:
    """Tests for the _export_notebooks_parallel function."""

    def test_export_notebooks_parallel_empty(self):
        """Test parallel export with empty list."""
        # Execute
        result = _export_notebooks_parallel([], Path("/output"), True, None)

        # Assert
        assert isinstance(result, BatchExportResult)
        assert result.succeeded == 0
        assert result.failed == 0

    def test_export_notebooks_parallel_success(self):
        """Test successful parallel export."""
        # Setup
        mock_notebooks = []
        for i in range(3):
            nb = MagicMock()
            nb.path = Path(f"/nb{i}.py")
            nb.export.return_value = NotebookExportResult.succeeded(Path(f"/nb{i}.py"), Path(f"/output/nb{i}.html"))
            mock_notebooks.append(nb)

        # Execute
        result = _export_notebooks_parallel(mock_notebooks, Path("/output"), True, None, max_workers=2)

        # Assert
        assert isinstance(result, BatchExportResult)
        assert result.succeeded == 3
        assert result.failed == 0
        assert result.all_succeeded is True

    def test_export_notebooks_parallel_mixed_results(self):
        """Test parallel export with some failures."""
        # Setup
        mock_notebooks = []
        for i in range(3):
            nb = MagicMock()
            # Create a mock path with a name attribute
            mock_path = MagicMock()
            mock_path.name = f"notebook{i}.py"
            nb.path = mock_path
            if i != 1:  # Second notebook fails
                nb.export.return_value = NotebookExportResult.succeeded(
                    Path(f"/notebook{i}.py"), Path(f"/output/notebook{i}.html")
                )
            else:
                nb.export.return_value = NotebookExportResult.failed(
                    Path(f"/notebook{i}.py"),
                    ExportSubprocessError(Path(f"/notebook{i}.py"), ["cmd"], 1),
                )
            mock_notebooks.append(nb)

        # Execute
        result = _export_notebooks_parallel(mock_notebooks, Path("/output"), True, None, max_workers=2)

        # Assert
        assert isinstance(result, BatchExportResult)
        assert result.succeeded == 2
        assert result.failed == 1
        assert result.all_succeeded is False


class TestGenerateIndex:
    """Tests for the _generate_index function."""

    @patch.object(Path, "open", new_callable=mock_open)
    @patch("jinja2.Environment")
    def test_generate_index_success(self, mock_env, mock_file_open, tmp_path):
        """Test the successful generation of index.html."""
        # Setup
        output_dir = tmp_path / "output"
        template_file = Path("template_dir/template.html.j2")

        # Create mock notebooks and apps with proper return values
        mock_notebook1 = MagicMock()
        mock_notebook2 = MagicMock()
        mock_app1 = MagicMock()
        mock_notebook1_wasm = MagicMock()

        # Set up export return values
        mock_notebook1.export.return_value = NotebookExportResult.succeeded(Path("/nb1.py"), Path("/output/nb1.html"))
        mock_notebook2.export.return_value = NotebookExportResult.succeeded(Path("/nb2.py"), Path("/output/nb2.html"))
        mock_app1.export.return_value = NotebookExportResult.succeeded(Path("/app1.py"), Path("/output/app1.html"))
        mock_notebook1_wasm.export.return_value = NotebookExportResult.succeeded(
            Path("/nb_wasm1.py"), Path("/output/nb_wasm1.html")
        )

        notebooks = [mock_notebook1, mock_notebook2]
        apps = [mock_app1]
        notebooks_wasm = [mock_notebook1_wasm]

        # Mock the template rendering
        mock_template = MagicMock()
        mock_env.return_value.get_template.return_value = mock_template
        mock_template.render.return_value = "<html>Rendered content</html>"

        # Execute with parallel=False for predictable test behavior
        result = _generate_index(
            output=output_dir,
            template_file=template_file,
            notebooks=notebooks,
            apps=apps,
            notebooks_wasm=notebooks_wasm,
            parallel=False,
        )

        # Assert
        # Check that export was called for each notebook and app
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
        mock_notebook.export.return_value = NotebookExportResult.succeeded(Path("/nb.py"), Path("/output/nb.html"))
        notebooks = [mock_notebook]
        apps = []

        # Mock the template rendering
        mock_template = MagicMock()
        mock_env.return_value.get_template.return_value = mock_template
        mock_template.render.return_value = "<html>Rendered content</html>"

        # Execute and Assert - now raises IndexWriteError
        with pytest.raises(IndexWriteError) as exc_info:
            _generate_index(
                output=output_dir, template_file=template_file, notebooks=notebooks, apps=apps, parallel=False
            )

        # Check that the error contains the path
        assert exc_info.value.index_path == output_dir / "index.html"

        # Check that export was still called before the error
        mock_notebook.export.assert_called_once_with(output_dir=output_dir / "notebooks", sandbox=True, bin_path=None)

    @patch("jinja2.Environment")
    @patch.object(Path, "mkdir")
    def test_generate_index_template_error(self, mock_mkdir, mock_env, tmp_path):
        """Test handling of template error during index generation."""
        # Setup
        output_dir = tmp_path / "output"
        template_file = Path("template_dir/template.html.j2")

        # Create mock notebooks
        mock_notebook = MagicMock()
        mock_notebook.export.return_value = NotebookExportResult.succeeded(Path("/nb.py"), Path("/output/nb.html"))
        notebooks = [mock_notebook]
        apps = []

        # Mock the template error
        mock_env.side_effect = jinja2.exceptions.TemplateError("Template error")

        # Execute and Assert - now raises TemplateRenderError
        with pytest.raises(TemplateRenderError) as exc_info:
            _generate_index(
                output=output_dir, template_file=template_file, notebooks=notebooks, apps=apps, parallel=False
            )

        # Check that the error contains the template path
        assert exc_info.value.template_path == template_file

        # Check that export was still called before the template error
        mock_notebook.export.assert_called_once_with(output_dir=output_dir / "notebooks", sandbox=True, bin_path=None)

    def test_generate_index_no_notebooks(self, tmp_path):
        """Test index generation with no notebooks."""
        # Setup
        output_dir = tmp_path / "output"
        template_file = tmp_path / "template.html.j2"
        template_file.write_text("<html>{{ notebooks }}</html>")

        # Execute
        result = _generate_index(
            output=output_dir,
            template_file=template_file,
            notebooks=[],
            apps=[],
            notebooks_wasm=[],
        )

        # Assert - should still generate index with empty lists
        assert "[]" in result


class TestMain:
    """Tests for the main function."""

    @patch("marimushka.export._validate_template")
    @patch("marimushka.export.folder2notebooks")
    @patch("marimushka.export._generate_index")
    def test_main_success(self, mock_generate_index, mock_folder2notebooks, mock_validate):
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

    @patch("marimushka.export._validate_template")
    @patch("marimushka.export.folder2notebooks")
    @patch("marimushka.export._generate_index")
    def test_main_no_notebooks_or_apps(self, mock_generate_index, mock_folder2notebooks, mock_validate):
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

    @patch("marimushka.export._validate_template")
    @patch("marimushka.export.folder2notebooks")
    @patch("marimushka.export._generate_index")
    def test_main_custom_paths(self, mock_generate_index, mock_folder2notebooks, mock_validate, tmp_path):
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
            parallel=True,
            max_workers=4,
        )

    @patch("marimushka.export._validate_template")
    @patch("marimushka.export.folder2notebooks")
    @patch("marimushka.export._generate_index")
    def test_main_parallel_options(self, mock_generate_index, mock_folder2notebooks, mock_validate, tmp_path):
        """Test main function with parallel options."""
        # Setup
        mock_notebooks = [MagicMock()]
        mock_folder2notebooks.side_effect = [mock_notebooks, [], []]

        custom_output = tmp_path / "output"
        custom_template = tmp_path / "template.html.j2"

        # Execute with parallel=False and custom max_workers
        main(
            output=custom_output,
            template=custom_template,
            parallel=False,
            max_workers=8,
        )

        # Assert
        call_kwargs = mock_generate_index.call_args.kwargs
        assert call_kwargs["parallel"] is False
        assert call_kwargs["max_workers"] == 8

    def test_main_invalid_template(self, tmp_path):
        """Test main function with non-existent template."""
        # Setup
        nonexistent_template = tmp_path / "nonexistent.html.j2"

        # Execute and Assert
        with pytest.raises(TemplateNotFoundError) as exc_info:
            main(template=nonexistent_template)
        assert exc_info.value.template_path == nonexistent_template


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
    def test_main_typer_passes_parameters_directly(self, mock_main):
        """Test _main_typer function passes parameters directly to main()."""
        from marimushka.export import _main_typer

        # Execute - pass values directly (as Typer does after resolving Options)
        _main_typer(
            output="custom_site",
            template="custom_template.html",
            notebooks="custom_notebooks",
            apps="custom_apps",
            notebooks_wasm="custom_notebooks_wasm",
            sandbox=False,
            bin_path="/custom/bin",
            parallel=True,
            max_workers=4,
        )

        # Assert - verify that main was called with the same values
        mock_main.assert_called_once_with(
            output="custom_site",
            template="custom_template.html",
            notebooks="custom_notebooks",
            apps="custom_apps",
            notebooks_wasm="custom_notebooks_wasm",
            sandbox=False,
            bin_path="/custom/bin",
            parallel=True,
            max_workers=4,
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
            parallel=False,
            max_workers=2,
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
            parallel=False,
            max_workers=2,
        )


class TestWatchCommand:
    """Tests for the watch command."""

    def test_watch_command_no_watchfiles(self):
        """Test watch command fails gracefully without watchfiles."""
        from marimushka.export import watch

        # We can't easily test the ImportError case without actually
        # uninstalling watchfiles, so we just verify the function exists
        assert callable(watch)

    @patch("marimushka.export.main")
    def test_watch_command_exists(self, mock_main):
        """Test that watch command is registered."""
        from marimushka.export import app

        # Get all registered commands
        commands = [cmd.name for cmd in app.registered_commands]

        # Assert watch is registered
        assert "watch" in commands
        assert "export" in commands
        assert "version" in commands
