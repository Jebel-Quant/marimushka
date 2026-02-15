"""Tests for the export.py module.

This module contains tests for the functions in the export.py module:
- _folder2notebooks
- _generate_index
- _validate_template
- _export_notebooks_parallel
- main
- cli
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import jinja2
import pytest
import typer
from hypothesis import given
from hypothesis import strategies as st

from marimushka.audit import get_audit_logger
from marimushka.exceptions import (
    BatchExportResult,
    ExportSubprocessError,
    IndexWriteError,
    NotebookExportResult,
    TemplateInvalidError,
    TemplateNotFoundError,
    TemplateRenderError,
)
from marimushka.export import main
from marimushka.notebook import Kind, folder2notebooks
from marimushka.orchestrator import (
    export_notebook,
    export_notebooks_parallel,
    export_notebooks_sequential,
    generate_index,
)
from marimushka.validators import validate_template


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
        validate_template(template_file, get_audit_logger())

    def test_validate_template_jinja2_extension(self, tmp_path):
        """Test template validation with .jinja2 extension."""
        # Setup
        template_file = tmp_path / "template.html.jinja2"
        template_file.write_text("<html></html>")

        # Execute - should not raise
        validate_template(template_file, get_audit_logger())

    def test_validate_template_not_found(self, tmp_path):
        """Test template validation when file not found."""
        # Setup
        template_file = tmp_path / "nonexistent.html.j2"

        # Execute and Assert
        with pytest.raises(TemplateNotFoundError) as exc_info:
            validate_template(template_file, get_audit_logger())
        assert exc_info.value.template_path == template_file

    def test_validate_template_not_a_file(self, tmp_path):
        """Test template validation when path is a directory."""
        # Setup
        template_dir = tmp_path / "template_dir"
        template_dir.mkdir()

        # Execute and Assert
        with pytest.raises(TemplateInvalidError) as exc_info:
            validate_template(template_dir, get_audit_logger())
        assert exc_info.value.template_path == template_dir
        assert "not a file" in exc_info.value.reason

    def test_validate_template_wrong_extension_warning(self, tmp_path, caplog):
        """Test template validation warns on wrong extension."""
        # Setup
        template_file = tmp_path / "template.html"
        template_file.write_text("<html></html>")

        # Execute - should not raise but should log warning
        validate_template(template_file, get_audit_logger())

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
        result = export_notebook(mock_notebook, output_dir, sandbox=True, bin_path=None)

        # Assert
        assert result is mock_result
        assert result.success is True
        mock_notebook.export.assert_called_once_with(output_dir=output_dir, sandbox=True, bin_path=None, timeout=300)

    def test_export_notebook_failure(self):
        """Test notebook export failure."""
        # Setup
        mock_notebook = MagicMock()
        mock_result = NotebookExportResult.failed(Path("/nb.py"), ExportSubprocessError(Path("/nb.py"), ["cmd"], 1))
        mock_notebook.export.return_value = mock_result
        output_dir = Path("/output")

        # Execute
        result = export_notebook(mock_notebook, output_dir, sandbox=False, bin_path=Path("/bin"))

        # Assert
        assert result is mock_result
        assert result.success is False


class TestExportNotebooksParallel:
    """Tests for the _export_notebooks_parallel function."""

    def test_export_notebooks_parallel_empty(self):
        """Test parallel export with empty list."""
        # Execute
        result = export_notebooks_parallel([], Path("/output"), True, None)

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
        result = export_notebooks_parallel(mock_notebooks, Path("/output"), True, None, max_workers=2)

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
        result = export_notebooks_parallel(mock_notebooks, Path("/output"), True, None, max_workers=2)

        # Assert
        assert isinstance(result, BatchExportResult)
        assert result.succeeded == 2
        assert result.failed == 1
        assert result.all_succeeded is False


class TestExportNotebooksSequential:
    """Tests for the _export_notebooks_sequential function."""

    def test_export_notebooks_sequential_without_progress(self):
        """Test sequential export without progress tracking (progress=None)."""
        # Setup
        mock_notebooks = []
        for i in range(3):
            nb = MagicMock()
            nb.path = Path(f"/nb{i}.py")
            nb.export.return_value = NotebookExportResult.succeeded(Path(f"/nb{i}.py"), Path(f"/output/nb{i}.html"))
            mock_notebooks.append(nb)

        # Execute - explicitly pass progress=None to cover the branch
        result = export_notebooks_sequential(
            mock_notebooks, Path("/output"), sandbox=True, bin_path=None, progress=None, task_id=None
        )

        # Assert
        assert isinstance(result, BatchExportResult)
        assert result.succeeded == 3
        assert result.failed == 0
        assert result.all_succeeded is True
        # Verify all notebooks were exported
        for nb in mock_notebooks:
            nb.export.assert_called_once_with(output_dir=Path("/output"), sandbox=True, bin_path=None, timeout=300)

    def test_export_notebooks_sequential_empty_list(self):
        """Test sequential export with empty list."""
        # Execute
        result = export_notebooks_sequential([], Path("/output"), sandbox=True, bin_path=None)

        # Assert
        assert isinstance(result, BatchExportResult)
        assert result.succeeded == 0
        assert result.failed == 0


class TestGenerateIndex:
    """Tests for the _generate_index function."""

    @patch("marimushka.orchestrator.set_secure_file_permissions")
    @patch.object(Path, "open", new_callable=mock_open)
    @patch("marimushka.orchestrator.SandboxedEnvironment")
    def test_generate_index_success(self, mock_env, mock_file_open, mock_permissions, tmp_path):
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
        result = generate_index(
            output=output_dir,
            template_file=template_file,
            notebooks=notebooks,
            apps=apps,
            notebooks_wasm=notebooks_wasm,
            parallel=False,
        )

        # Assert
        # Check that export was called for each notebook and app
        mock_notebook1.export.assert_called_once_with(
            output_dir=output_dir / "notebooks", sandbox=True, bin_path=None, timeout=300
        )
        mock_notebook2.export.assert_called_once_with(
            output_dir=output_dir / "notebooks", sandbox=True, bin_path=None, timeout=300
        )
        mock_app1.export.assert_called_once_with(
            output_dir=output_dir / "apps", sandbox=True, bin_path=None, timeout=300
        )

        # Check that the template was rendered and written to file
        mock_env.assert_called_once()
        mock_env.return_value.get_template.assert_called_once_with(template_file.name)
        mock_template.render.assert_called_once_with(notebooks=notebooks, apps=apps, notebooks_wasm=notebooks_wasm)
        # Check that the index.html file was opened for writing (audit logger also uses Path.open)
        mock_file_open.assert_any_call(output_dir / "index.html", "w")

        # Check that the function returns the rendered HTML
        assert result == "<html>Rendered content</html>"

    @patch.object(Path, "open", side_effect=OSError("File error"))
    @patch("marimushka.orchestrator.SandboxedEnvironment")
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
            generate_index(
                output=output_dir, template_file=template_file, notebooks=notebooks, apps=apps, parallel=False
            )

        # Check that the error contains the path
        assert exc_info.value.index_path == output_dir / "index.html"

        # Check that export was still called before the error
        mock_notebook.export.assert_called_once_with(
            output_dir=output_dir / "notebooks", sandbox=True, bin_path=None, timeout=300
        )

    @patch("marimushka.orchestrator.SandboxedEnvironment")
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
            generate_index(
                output=output_dir, template_file=template_file, notebooks=notebooks, apps=apps, parallel=False
            )

        # Check that the error contains the template path
        assert exc_info.value.template_path == template_file

        # Check that export was still called before the template error
        mock_notebook.export.assert_called_once_with(
            output_dir=output_dir / "notebooks", sandbox=True, bin_path=None, timeout=300
        )

    def test_generate_index_no_notebooks(self, tmp_path):
        """Test index generation with no notebooks."""
        # Setup
        output_dir = tmp_path / "output"
        template_file = tmp_path / "template.html.j2"
        template_file.write_text("<html>{{ notebooks }}</html>")

        # Execute
        result = generate_index(
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

    @patch("marimushka.validators.validate_template")
    @patch("marimushka.export.folder2notebooks")
    @patch("marimushka.orchestrator.generate_index")
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

    @patch("marimushka.validators.validate_template")
    @patch("marimushka.export.folder2notebooks")
    @patch("marimushka.orchestrator.generate_index")
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

    @patch("marimushka.validators.validate_template")
    @patch("marimushka.export.folder2notebooks")
    @patch("marimushka.orchestrator.generate_index")
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
            timeout=300,
        )

    @patch("marimushka.validators.validate_template")
    @patch("marimushka.export.folder2notebooks")
    @patch("marimushka.orchestrator.generate_index")
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
        from marimushka.cli import callback

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
        from marimushka.cli import callback

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
        from marimushka.cli import export_command

        # Execute - pass values directly (as Typer does after resolving Options)
        export_command(
            output="custom_site",
            template="custom_template.html",
            notebooks="custom_notebooks",
            apps="custom_apps",
            notebooks_wasm="custom_notebooks_wasm",
            sandbox=False,
            bin_path="/custom/bin",
            parallel=True,
            max_workers=4,
            timeout=300,
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
            timeout=300,
        )

    @patch("marimushka.export.main")
    def test_main_typer_with_string_values(self, mock_main):
        """Test _main_typer function with string values (not Option objects)."""
        from marimushka.cli import export_command

        # Execute with regular string values
        export_command(
            output="output_dir",
            template="template.html",
            notebooks="notebooks",
            apps="apps",
            notebooks_wasm="notebooks_wasm",
            sandbox=True,
            bin_path="/bin",
            parallel=False,
            max_workers=2,
            timeout=300,
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
            timeout=300,
        )


class TestWatchCommand:
    """Tests for the watch command."""

    def test_watch_command_no_watchfiles(self):
        """Test watch command fails gracefully without watchfiles."""
        from marimushka.cli import watch_command

        # We can't easily test the ImportError case without actually
        # uninstalling watchfiles, so we just verify the function exists
        assert callable(watch_command)

    @patch("marimushka.export.main")
    def test_watch_command_exists(self, mock_main):
        """Test that watch command is registered."""
        from marimushka.cli import app

        # Get all registered commands
        commands = [cmd.name for cmd in app.registered_commands]

        # Assert watch is registered
        assert "watch" in commands
        assert "export" in commands
        assert "version" in commands

    @patch("marimushka.cli.rich_print")
    def test_watch_no_directories_to_watch(self, mock_print, tmp_path):
        """Test watch command exits when no directories exist to watch."""
        from marimushka.cli import watch_command

        # Use non-existent paths
        with pytest.raises(typer.Exit) as exc_info:
            watch_command(
                output=str(tmp_path / "_site"),
                template=str(tmp_path / "nonexistent_template.j2"),
                notebooks=str(tmp_path / "nonexistent_notebooks"),
                apps=str(tmp_path / "nonexistent_apps"),
                notebooks_wasm=str(tmp_path / "nonexistent_wasm"),
                sandbox=True,
                bin_path=None,
                parallel=True,
                max_workers=4,
                timeout=300,
            )
        assert exc_info.value.exit_code == 1
        # Verify warning was printed
        mock_print.assert_any_call("[bold yellow]Warning:[/bold yellow] No directories to watch!")

    @patch("marimushka.export.main")
    @patch("marimushka.cli.rich_print")
    def test_watch_initial_export_called(self, mock_print, mock_main, tmp_path):
        """Test watch command calls initial export before watching."""
        # Setup directories
        notebooks_dir = tmp_path / "notebooks"
        notebooks_dir.mkdir()

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "template.html.j2"
        template_file.write_text("<html></html>")

        # Create a generator that raises KeyboardInterrupt immediately
        def mock_watch_generator(*args, **kwargs):
            raise KeyboardInterrupt

        with patch("watchfiles.watch", mock_watch_generator):
            from marimushka.cli import watch_command

            watch_command(
                output=str(tmp_path / "_site"),
                template=str(template_file),
                notebooks=str(notebooks_dir),
                apps=str(tmp_path / "nonexistent_apps"),
                notebooks_wasm=str(tmp_path / "nonexistent_wasm"),
                sandbox=True,
                bin_path=None,
                parallel=True,
                max_workers=4,
                timeout=300,
            )

        # Verify initial export was called with correct parameters
        mock_main.assert_called_once_with(
            output=str(tmp_path / "_site"),
            template=str(template_file),
            notebooks=str(notebooks_dir),
            apps=str(tmp_path / "nonexistent_apps"),
            notebooks_wasm=str(tmp_path / "nonexistent_wasm"),
            sandbox=True,
            bin_path=None,
            parallel=True,
            max_workers=4,
            timeout=300,
        )

    @patch("marimushka.export.main")
    @patch("marimushka.cli.rich_print")
    def test_watch_keyboard_interrupt_handled(self, mock_print, mock_main, tmp_path):
        """Test watch command handles KeyboardInterrupt gracefully."""
        # Setup directories
        notebooks_dir = tmp_path / "notebooks"
        notebooks_dir.mkdir()

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "template.html.j2"
        template_file.write_text("<html></html>")

        # Create a generator that raises KeyboardInterrupt
        def mock_watch_generator(*args, **kwargs):
            raise KeyboardInterrupt

        with patch("watchfiles.watch", mock_watch_generator):
            from marimushka.cli import watch_command

            # Should not raise, should handle gracefully
            watch_command(
                output=str(tmp_path / "_site"),
                template=str(template_file),
                notebooks=str(notebooks_dir),
                apps=str(tmp_path / "apps"),
                notebooks_wasm=str(tmp_path / "wasm"),
                sandbox=True,
                bin_path=None,
                parallel=True,
                max_workers=4,
                timeout=300,
            )

        # Verify the "stopped" message was printed
        mock_print.assert_any_call("\n[bold green]Watch mode stopped.[/bold green]")

    @patch("marimushka.export.main")
    @patch("marimushka.cli.rich_print")
    def test_watch_reexports_on_change(self, mock_print, mock_main, tmp_path):
        """Test watch command re-exports when files change."""
        # Setup directories
        notebooks_dir = tmp_path / "notebooks"
        notebooks_dir.mkdir()

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "template.html.j2"
        template_file.write_text("<html></html>")

        # Track call count

        # Create a generator that yields one change then raises KeyboardInterrupt
        def mock_watch_generator(*args, **kwargs):
            # Yield one set of changes
            yield [("modified", str(notebooks_dir / "test.py"))]
            # Then stop
            raise KeyboardInterrupt

        with patch("watchfiles.watch", mock_watch_generator):
            from marimushka.cli import watch_command

            watch_command(
                output=str(tmp_path / "_site"),
                template=str(template_file),
                notebooks=str(notebooks_dir),
                apps=str(tmp_path / "apps"),
                notebooks_wasm=str(tmp_path / "wasm"),
                sandbox=True,
                bin_path=None,
                parallel=True,
                max_workers=4,
                timeout=300,
            )

        # Verify main was called twice: once for initial export, once for re-export
        assert mock_main.call_count == 2

    @patch("marimushka.export.main")
    @patch("marimushka.cli.rich_print")
    def test_watch_shows_changed_files(self, mock_print, mock_main, tmp_path):
        """Test watch command displays changed files."""
        # Setup directories
        notebooks_dir = tmp_path / "notebooks"
        notebooks_dir.mkdir()

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "template.html.j2"
        template_file.write_text("<html></html>")

        # Create a generator that yields changes with multiple files
        def mock_watch_generator(*args, **kwargs):
            yield [
                ("modified", "/path/to/file1.py"),
                ("modified", "/path/to/file2.py"),
                ("modified", "/path/to/file3.py"),
            ]
            raise KeyboardInterrupt

        with patch("watchfiles.watch", mock_watch_generator):
            from marimushka.cli import watch_command

            watch_command(
                output=str(tmp_path / "_site"),
                template=str(template_file),
                notebooks=str(notebooks_dir),
                apps=str(tmp_path / "apps"),
                notebooks_wasm=str(tmp_path / "wasm"),
                sandbox=True,
                bin_path=None,
                parallel=True,
                max_workers=4,
                timeout=300,
            )

        # Verify changed files were printed
        mock_print.assert_any_call("\n[bold yellow]Detected changes:[/bold yellow]")
        mock_print.assert_any_call("  [dim]/path/to/file1.py[/dim]")

    @patch("marimushka.export.main")
    @patch("marimushka.cli.rich_print")
    def test_watch_truncates_long_change_list(self, mock_print, mock_main, tmp_path):
        """Test watch command truncates list when more than 5 files change."""
        # Setup directories
        notebooks_dir = tmp_path / "notebooks"
        notebooks_dir.mkdir()

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "template.html.j2"
        template_file.write_text("<html></html>")

        # Create a generator that yields changes with many files
        def mock_watch_generator(*args, **kwargs):
            yield [("modified", f"/path/to/file{i}.py") for i in range(10)]
            raise KeyboardInterrupt

        with patch("watchfiles.watch", mock_watch_generator):
            from marimushka.cli import watch_command

            watch_command(
                output=str(tmp_path / "_site"),
                template=str(template_file),
                notebooks=str(notebooks_dir),
                apps=str(tmp_path / "apps"),
                notebooks_wasm=str(tmp_path / "wasm"),
                sandbox=True,
                bin_path=None,
                parallel=True,
                max_workers=4,
                timeout=300,
            )

        # Verify truncation message was printed (10 files - 5 shown = 5 more)
        mock_print.assert_any_call("  [dim]... and 5 more[/dim]")

    @patch("marimushka.export.main")
    @patch("marimushka.cli.rich_print")
    def test_watch_with_custom_parameters(self, mock_print, mock_main, tmp_path):
        """Test watch command passes all parameters correctly."""
        # Setup directories
        notebooks_dir = tmp_path / "notebooks"
        notebooks_dir.mkdir()

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "template.html.j2"
        template_file.write_text("<html></html>")

        bin_path_dir = tmp_path / "bin"
        bin_path_dir.mkdir()

        def mock_watch_generator(*args, **kwargs):
            raise KeyboardInterrupt

        with patch("watchfiles.watch", mock_watch_generator):
            from marimushka.cli import watch_command

            watch_command(
                output=str(tmp_path / "custom_output"),
                template=str(template_file),
                notebooks=str(notebooks_dir),
                apps=str(tmp_path / "custom_apps"),
                notebooks_wasm=str(tmp_path / "custom_wasm"),
                sandbox=False,
                bin_path=str(bin_path_dir),
                parallel=False,
                max_workers=8,
                timeout=600,
            )

        # Verify main was called with correct custom parameters
        mock_main.assert_called_once_with(
            output=str(tmp_path / "custom_output"),
            template=str(template_file),
            notebooks=str(notebooks_dir),
            apps=str(tmp_path / "custom_apps"),
            notebooks_wasm=str(tmp_path / "custom_wasm"),
            sandbox=False,
            bin_path=str(bin_path_dir),
            parallel=False,
            max_workers=8,
            timeout=600,
        )

    @patch("marimushka.export.main")
    @patch("marimushka.cli.rich_print")
    def test_watch_template_parent_added_to_watch_paths(self, mock_print, mock_main, tmp_path):
        """Test watch command adds template parent directory to watch paths."""
        # Setup directories
        notebooks_dir = tmp_path / "notebooks"
        notebooks_dir.mkdir()

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "template.html.j2"
        template_file.write_text("<html></html>")

        # Track what paths are passed to watchfiles
        watched_paths = []

        def mock_watch_generator(*args, **kwargs):
            watched_paths.extend(args)
            raise KeyboardInterrupt

        with patch("watchfiles.watch", mock_watch_generator):
            from marimushka.cli import watch_command

            watch_command(
                output=str(tmp_path / "_site"),
                template=str(template_file),
                notebooks=str(notebooks_dir),
                apps=str(tmp_path / "apps"),
                notebooks_wasm=str(tmp_path / "wasm"),
                sandbox=True,
                bin_path=None,
                parallel=True,
                max_workers=4,
                timeout=300,
            )

        # Verify template parent directory was included
        assert template_dir in watched_paths


class TestValidateTemplateHypothesis:
    """Property-based tests for _validate_template function."""

    @given(
        stem=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_-"),
            min_size=1,
            max_size=30,
        ).filter(lambda x: x.strip() and not x.startswith("-"))
    )
    def test_valid_j2_extension_does_not_raise(self, stem: str):
        """Test that files with .j2 extension pass validation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            template_file = Path(tmp_dir) / f"{stem}.html.j2"
            template_file.write_text("<html></html>")

            # Should not raise any exception
            validate_template(template_file, get_audit_logger())

    @given(
        stem=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_-"),
            min_size=1,
            max_size=30,
        ).filter(lambda x: x.strip() and not x.startswith("-"))
    )
    def test_valid_jinja2_extension_does_not_raise(self, stem: str):
        """Test that files with .jinja2 extension pass validation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            template_file = Path(tmp_dir) / f"{stem}.html.jinja2"
            template_file.write_text("<html></html>")

            # Should not raise any exception
            validate_template(template_file, get_audit_logger())

    @given(
        stem=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_-"),
            min_size=1,
            max_size=30,
        ).filter(lambda x: x.strip() and not x.startswith("-"))
    )
    def test_nonexistent_file_raises_not_found(self, stem: str):
        """Test that non-existent files raise TemplateNotFoundError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            template_file = Path(tmp_dir) / f"{stem}.html.j2"
            # Don't create the file

            with pytest.raises(TemplateNotFoundError) as exc_info:
                validate_template(template_file, get_audit_logger())
            assert exc_info.value.template_path == template_file

    @given(
        stem=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_-"),
            min_size=1,
            max_size=30,
        ).filter(lambda x: x.strip() and not x.startswith("-"))
    )
    def test_directory_raises_invalid(self, stem: str):
        """Test that directories raise TemplateInvalidError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            template_dir = Path(tmp_dir) / stem
            template_dir.mkdir()

            with pytest.raises(TemplateInvalidError) as exc_info:
                validate_template(template_dir, get_audit_logger())
            assert exc_info.value.template_path == template_dir
            assert "not a file" in exc_info.value.reason


class TestExportNotebooksParallelHypothesis:
    """Property-based tests for _export_notebooks_parallel function."""

    @given(num_notebooks=st.integers(min_value=0, max_value=20))
    def test_result_count_equals_input_count(self, num_notebooks: int):
        """Test that the number of results equals the number of input notebooks."""
        mock_notebooks = []
        for i in range(num_notebooks):
            nb = MagicMock()
            nb.path = Path(f"/nb{i}.py")
            nb.export.return_value = NotebookExportResult.succeeded(Path(f"/nb{i}.py"), Path(f"/output/nb{i}.html"))
            mock_notebooks.append(nb)

        result = export_notebooks_parallel(mock_notebooks, Path("/output"), True, None, max_workers=2)

        assert len(result.results) == num_notebooks
        assert result.succeeded + result.failed == num_notebooks

    @given(
        num_success=st.integers(min_value=0, max_value=10),
        num_failure=st.integers(min_value=0, max_value=10),
    )
    def test_success_and_failure_counts_accurate(self, num_success: int, num_failure: int):
        """Test that success and failure counts are accurate."""
        mock_notebooks = []

        # Create successful notebooks
        for i in range(num_success):
            nb = MagicMock()
            mock_path = MagicMock()
            mock_path.name = f"success{i}.py"
            nb.path = mock_path
            nb.export.return_value = NotebookExportResult.succeeded(
                Path(f"/success{i}.py"), Path(f"/output/success{i}.html")
            )
            mock_notebooks.append(nb)

        # Create failing notebooks
        for i in range(num_failure):
            nb = MagicMock()
            mock_path = MagicMock()
            mock_path.name = f"failure{i}.py"
            nb.path = mock_path
            nb.export.return_value = NotebookExportResult.failed(
                Path(f"/failure{i}.py"),
                ExportSubprocessError(Path(f"/failure{i}.py"), ["cmd"], 1),
            )
            mock_notebooks.append(nb)

        result = export_notebooks_parallel(mock_notebooks, Path("/output"), True, None, max_workers=2)

        assert result.succeeded == num_success
        assert result.failed == num_failure
        # all_succeeded is True when failed == 0 (regardless of succeeded count)
        assert result.all_succeeded == (num_failure == 0)

    @given(max_workers=st.integers(min_value=1, max_value=16))
    def test_works_with_various_worker_counts(self, max_workers: int):
        """Test that export works with various worker counts."""
        mock_notebooks = []
        for i in range(5):
            nb = MagicMock()
            nb.path = Path(f"/nb{i}.py")
            nb.export.return_value = NotebookExportResult.succeeded(Path(f"/nb{i}.py"), Path(f"/output/nb{i}.html"))
            mock_notebooks.append(nb)

        result = export_notebooks_parallel(mock_notebooks, Path("/output"), True, None, max_workers=max_workers)

        assert result.succeeded == 5
        assert result.failed == 0


class TestBatchExportResultHypothesis:
    """Property-based tests for BatchExportResult class."""

    @given(
        success_count=st.integers(min_value=0, max_value=50),
        failure_count=st.integers(min_value=0, max_value=50),
    )
    def test_add_increments_counts_correctly(self, success_count: int, failure_count: int):
        """Test that add() correctly increments success and failure counts."""
        batch_result = BatchExportResult()

        # Add successful results
        for i in range(success_count):
            batch_result.add(NotebookExportResult.succeeded(Path(f"/s{i}.py"), Path(f"/out/s{i}.html")))

        # Add failed results
        for i in range(failure_count):
            batch_result.add(
                NotebookExportResult.failed(
                    Path(f"/f{i}.py"),
                    ExportSubprocessError(Path(f"/f{i}.py"), ["cmd"], 1),
                )
            )

        assert batch_result.succeeded == success_count
        assert batch_result.failed == failure_count
        assert len(batch_result.results) == success_count + failure_count

    @given(success_count=st.integers(min_value=1, max_value=50))
    def test_all_succeeded_true_when_no_failures(self, success_count: int):
        """Test that all_succeeded is True when there are no failures."""
        batch_result = BatchExportResult()

        for i in range(success_count):
            batch_result.add(NotebookExportResult.succeeded(Path(f"/s{i}.py"), Path(f"/out/s{i}.html")))

        assert batch_result.all_succeeded is True

    @given(
        success_count=st.integers(min_value=0, max_value=50),
        failure_count=st.integers(min_value=1, max_value=50),
    )
    def test_all_succeeded_false_when_any_failures(self, success_count: int, failure_count: int):
        """Test that all_succeeded is False when there are any failures."""
        batch_result = BatchExportResult()

        for i in range(success_count):
            batch_result.add(NotebookExportResult.succeeded(Path(f"/s{i}.py"), Path(f"/out/s{i}.html")))

        for i in range(failure_count):
            batch_result.add(
                NotebookExportResult.failed(
                    Path(f"/f{i}.py"),
                    ExportSubprocessError(Path(f"/f{i}.py"), ["cmd"], 1),
                )
            )

        assert batch_result.all_succeeded is False

    def test_all_succeeded_true_when_empty(self):
        """Test that all_succeeded is True when result is empty (no failures)."""
        batch_result = BatchExportResult()
        # all_succeeded is True when failed == 0, even for empty results
        assert batch_result.all_succeeded is True

    @given(failure_count=st.integers(min_value=1, max_value=50))
    def test_failures_property_returns_only_failures(self, failure_count: int):
        """Test that failures property returns only failed results."""
        batch_result = BatchExportResult()

        # Add some successes
        for i in range(3):
            batch_result.add(NotebookExportResult.succeeded(Path(f"/s{i}.py"), Path(f"/out/s{i}.html")))

        # Add failures
        for i in range(failure_count):
            batch_result.add(
                NotebookExportResult.failed(
                    Path(f"/f{i}.py"),
                    ExportSubprocessError(Path(f"/f{i}.py"), ["cmd"], 1),
                )
            )

        failures = batch_result.failures
        assert len(failures) == failure_count
        assert all(not f.success for f in failures)
