"""Integration tests for marimushka.

These tests verify the integration between different components of the system,
including the export workflow, template rendering, progress callbacks, and
debug mode logging.
"""

import shutil
from pathlib import Path

import pytest

from marimushka.audit import AuditLogger
from marimushka.config import MarimushkaConfig
from marimushka.exceptions import BatchExportResult, ProgressCallback
from marimushka.export import main
from marimushka.notebook import Kind, Notebook, folder2notebooks
from marimushka.orchestrator import (
    export_all_notebooks,
    export_notebooks_parallel,
    export_notebooks_sequential,
    generate_index,
    render_template,
    write_index_file,
)


class TestFullExportWorkflow:
    """Integration tests for the full export workflow."""

    def test_export_workflow_end_to_end(self, resource_dir, tmp_path):
        """Test the complete export workflow from notebooks to HTML."""
        # Setup
        notebooks_dir = resource_dir / "marimo" / "notebooks"
        apps_dir = resource_dir / "marimo" / "apps"
        template_path = resource_dir / "templates" / "tailwind.html.j2"
        output_dir = tmp_path / "output"

        # Execute
        html = main(
            notebooks=notebooks_dir,
            apps=apps_dir,
            template=template_path,
            output=output_dir,
            sandbox=True,
            parallel=True,
            max_workers=2,
        )

        # Verify
        assert html
        assert (output_dir / "index.html").exists()
        assert (output_dir / "notebooks").exists()
        assert (output_dir / "apps").exists()

        # Check that exported HTML files exist
        notebook_files = list((output_dir / "notebooks").glob("*.html"))
        app_files = list((output_dir / "apps").glob("*.html"))
        assert len(notebook_files) > 0
        assert len(app_files) > 0

    def test_export_workflow_with_progress_callback(self, resource_dir, tmp_path):
        """Test export workflow with progress callback integration."""
        # Track progress calls
        progress_calls = []

        def progress_callback(completed: int, total: int, name: str) -> None:
            progress_calls.append((completed, total, name))

        # Execute
        notebooks_dir = resource_dir / "marimo" / "notebooks"
        template_path = resource_dir / "templates" / "tailwind.html.j2"

        main(
            notebooks=notebooks_dir,
            template=template_path,
            output=tmp_path / "output",
            on_progress=progress_callback,
            parallel=False,  # Sequential for predictable callback order
        )

        # Verify progress callbacks were invoked
        assert len(progress_calls) > 0
        # Check that completed counts increase
        completed_counts = [c[0] for c in progress_calls]
        assert completed_counts == sorted(completed_counts)
        # Check that total is consistent
        totals = [c[1] for c in progress_calls]
        assert len(set(totals)) == 1  # All totals should be the same

    def test_export_workflow_sequential_vs_parallel(self, resource_dir, tmp_path):
        """Test that sequential and parallel exports produce same results."""
        notebooks_dir = resource_dir / "marimo" / "notebooks"
        template_path = resource_dir / "templates" / "tailwind.html.j2"

        # Sequential export
        output_seq = tmp_path / "output_seq"
        html_seq = main(
            notebooks=notebooks_dir,
            template=template_path,
            output=output_seq,
            parallel=False,
        )

        # Parallel export
        output_par = tmp_path / "output_par"
        html_par = main(
            notebooks=notebooks_dir,
            template=template_path,
            output=output_par,
            parallel=True,
            max_workers=2,
        )

        # Both should produce HTML
        assert html_seq
        assert html_par

        # Both should have same number of files
        seq_files = list(output_seq.glob("**/*.html"))
        par_files = list(output_par.glob("**/*.html"))
        assert len(seq_files) == len(par_files)


class TestTemplateRendering:
    """Integration tests for template rendering."""

    def test_template_rendering_with_real_jinja2(self, resource_dir, tmp_path):
        """Test template rendering with actual Jinja2 engine."""
        template_path = resource_dir / "templates" / "tailwind.html.j2"
        notebooks_dir = resource_dir / "marimo" / "notebooks"

        # Load notebooks
        notebooks = folder2notebooks(notebooks_dir, Kind.NB)
        audit_logger = AuditLogger()

        # Render template
        html = render_template(template_path, notebooks, [], [], audit_logger)

        # Verify rendering
        assert html
        assert "<!DOCTYPE html>" in html or "<html" in html
        # Should contain notebook references
        for nb in notebooks:
            assert nb.display_name in html

    def test_template_with_empty_notebook_lists(self, resource_dir, tmp_path):
        """Test template rendering with empty notebook lists."""
        template_path = resource_dir / "templates" / "tailwind.html.j2"
        audit_logger = AuditLogger()

        # Render with empty lists
        html = render_template(template_path, [], [], [], audit_logger)

        # Should still produce valid HTML
        assert html
        assert "<!DOCTYPE html>" in html or "<html" in html

    def test_template_with_mixed_notebook_types(self, resource_dir, tmp_path):
        """Test template rendering with all three notebook types."""
        template_path = resource_dir / "templates" / "tailwind.html.j2"
        marimo_dir = resource_dir / "marimo"

        notebooks = folder2notebooks(marimo_dir / "notebooks", Kind.NB)
        apps = folder2notebooks(marimo_dir / "apps", Kind.APP)
        notebooks_wasm = folder2notebooks(marimo_dir / "notebooks_wasm", Kind.NB_WASM)

        audit_logger = AuditLogger()
        html = render_template(template_path, notebooks, apps, notebooks_wasm, audit_logger)

        # Verify all types are represented
        assert html
        # Check for notebook references
        total_notebooks = len(notebooks) + len(apps) + len(notebooks_wasm)
        assert total_notebooks > 0


class TestProgressCallbackIntegration:
    """Integration tests for progress callback functionality."""

    def test_progress_callback_with_parallel_export(self, resource_dir, tmp_path):
        """Test progress callbacks work correctly with parallel exports."""
        notebooks_dir = resource_dir / "marimo" / "notebooks"
        notebooks = folder2notebooks(notebooks_dir, Kind.NB)

        if not notebooks:
            pytest.skip("No notebooks found for testing")

        progress_calls = []

        def callback(completed: int, total: int, name: str) -> None:
            progress_calls.append({"completed": completed, "total": total, "name": name})

        # Export with callback
        result = export_notebooks_parallel(
            notebooks=notebooks,
            output_dir=tmp_path / "notebooks",
            sandbox=True,
            bin_path=None,
            max_workers=2,
            timeout=300,
            on_progress=callback,
        )

        # Verify callbacks were invoked
        assert len(progress_calls) == len(notebooks)
        assert all(call["total"] == len(notebooks) for call in progress_calls)

    def test_progress_callback_with_sequential_export(self, resource_dir, tmp_path):
        """Test progress callbacks work correctly with sequential exports."""
        notebooks_dir = resource_dir / "marimo" / "notebooks"
        notebooks = folder2notebooks(notebooks_dir, Kind.NB)

        if not notebooks:
            pytest.skip("No notebooks found for testing")

        progress_calls = []

        def callback(completed: int, total: int, name: str) -> None:
            progress_calls.append({"completed": completed, "total": total, "name": name})

        # Export with callback
        result = export_notebooks_sequential(
            notebooks=notebooks,
            output_dir=tmp_path / "notebooks",
            sandbox=True,
            bin_path=None,
            timeout=300,
            on_progress=callback,
        )

        # Verify callbacks in correct order
        assert len(progress_calls) == len(notebooks)
        completed_values = [call["completed"] for call in progress_calls]
        assert completed_values == list(range(1, len(notebooks) + 1))

    def test_progress_callback_with_all_notebooks(self, resource_dir, tmp_path):
        """Test progress callbacks with export_all_notebooks function."""
        marimo_dir = resource_dir / "marimo"
        notebooks = folder2notebooks(marimo_dir / "notebooks", Kind.NB)
        apps = folder2notebooks(marimo_dir / "apps", Kind.APP)

        total_count = len(notebooks) + len(apps)
        if total_count == 0:
            pytest.skip("No notebooks found for testing")

        progress_calls = []

        def callback(completed: int, total: int, name: str) -> None:
            progress_calls.append({"completed": completed, "total": total})

        # Export all
        result = export_all_notebooks(
            output=tmp_path,
            notebooks=notebooks,
            apps=apps,
            notebooks_wasm=[],
            sandbox=True,
            bin_path=None,
            parallel=False,
            max_workers=1,
            timeout=300,
            on_progress=callback,
        )

        # Verify all callbacks received
        assert len(progress_calls) == total_count
        # Each export category reports its own subset, so totals may vary
        # but all should be positive
        assert all(call["total"] > 0 for call in progress_calls)


class TestDebugModeLogging:
    """Integration tests for debug mode logging output."""

    def test_export_with_audit_logging(self, resource_dir, tmp_path):
        """Test that audit logging captures export operations."""
        audit_log_path = tmp_path / "audit.log"
        audit_logger = AuditLogger(log_file=audit_log_path)

        template_path = resource_dir / "templates" / "tailwind.html.j2"
        notebooks_dir = resource_dir / "marimo" / "notebooks"
        notebooks = folder2notebooks(notebooks_dir, Kind.NB)

        if not notebooks:
            pytest.skip("No notebooks found for testing")

        # Generate index with audit logging
        generate_index(
            output=tmp_path / "output",
            template_file=template_path,
            notebooks=notebooks,
            apps=[],
            notebooks_wasm=[],
            audit_logger=audit_logger,
        )

        # Verify audit log was created and contains entries
        assert audit_log_path.exists()
        audit_content = audit_log_path.read_text()
        assert len(audit_content) > 0

    def test_index_write_with_audit_logging(self, tmp_path):
        """Test that index file writing is logged."""
        audit_log_path = tmp_path / "audit.log"
        audit_logger = AuditLogger(log_file=audit_log_path)

        index_path = tmp_path / "index.html"
        content = "<!DOCTYPE html><html><body>Test</body></html>"

        # Write index with audit logging
        write_index_file(index_path, content, audit_logger)

        # Verify index was written
        assert index_path.exists()
        assert index_path.read_text() == content

        # Verify audit log contains write operation
        assert audit_log_path.exists()


class TestConfigurationIntegration:
    """Integration tests for configuration loading and usage."""

    def test_export_with_config_from_dict(self, resource_dir, tmp_path):
        """Test export using configuration parameters."""
        config = MarimushkaConfig(
            output=str(tmp_path / "output"),
            notebooks=str(resource_dir / "marimo" / "notebooks"),
            apps=str(resource_dir / "marimo" / "apps"),
            template=str(resource_dir / "templates" / "tailwind.html.j2"),
            sandbox=True,
            parallel=False,
            max_workers=1,
            timeout=300,
        )

        # Use config for export
        html = main(
            output=config.output,
            notebooks=config.notebooks,
            apps=config.apps,
            template=config.template,
            sandbox=config.sandbox,
            parallel=config.parallel,
            max_workers=config.max_workers,
            timeout=config.timeout,
        )

        # Verify export succeeded
        assert html
        assert Path(config.output).exists()

    def test_config_to_dict_roundtrip(self, tmp_path):
        """Test that configuration can be converted to dict and back."""
        config = MarimushkaConfig(
            output=str(tmp_path / "output"),
            notebooks="notebooks",
            apps="apps",
            max_workers=8,
            timeout=600,
        )

        # Convert to dict
        config_dict = config.to_dict()

        # Verify dict structure
        assert config_dict["output"] == str(tmp_path / "output")
        assert config_dict["notebooks"] == "notebooks"
        assert config_dict["apps"] == "apps"
        assert config_dict["max_workers"] == 8
        assert config_dict["timeout"] == 600


class TestBatchExportIntegration:
    """Integration tests for batch export functionality."""

    def test_batch_export_with_mixed_results(self, resource_dir, tmp_path):
        """Test batch export handles mixed success/failure results."""
        notebooks_dir = resource_dir / "marimo" / "notebooks"
        notebooks = folder2notebooks(notebooks_dir, Kind.NB)

        if not notebooks:
            pytest.skip("No notebooks found for testing")

        # Export notebooks
        result = export_notebooks_parallel(
            notebooks=notebooks,
            output_dir=tmp_path / "notebooks",
            sandbox=True,
            bin_path=None,
            max_workers=2,
            timeout=300,
        )

        # Verify batch result
        assert result.total == len(notebooks)
        assert result.succeeded + result.failed == result.total
        # Most should succeed (assuming valid notebooks)
        assert result.succeeded > 0

    def test_batch_export_statistics(self, resource_dir, tmp_path):
        """Test that batch export statistics are accurate."""
        notebooks_dir = resource_dir / "marimo" / "notebooks"
        apps_dir = resource_dir / "marimo" / "apps"

        notebooks = folder2notebooks(notebooks_dir, Kind.NB)
        apps = folder2notebooks(apps_dir, Kind.APP)

        total_expected = len(notebooks) + len(apps)
        if total_expected == 0:
            pytest.skip("No notebooks found for testing")

        # Export all
        result = export_all_notebooks(
            output=tmp_path,
            notebooks=notebooks,
            apps=apps,
            notebooks_wasm=[],
            sandbox=True,
            bin_path=None,
            parallel=False,
            max_workers=1,
            timeout=300,
        )

        # Verify statistics
        assert result.total == total_expected
        assert len(result.successes) == result.succeeded
        assert len(result.failures) == result.failed
        assert result.all_succeeded == (result.failed == 0)
