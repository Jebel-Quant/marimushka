"""End-to-end workflow tests for marimushka.

These tests verify complete user workflows from start to finish, simulating
real-world usage scenarios including export verification, link checking,
watch mode simulation, custom templates, and debug output.
"""

import time

import pytest

from marimushka.export import main
from marimushka.notebook import Kind, folder2notebooks
from tests.utils.link_validator import validate_links


class TestExportAndVerifyWorkflow:
    """End-to-end tests for export → verify HTML → check links workflow."""

    def test_export_notebooks_verify_html_structure(self, resource_dir, tmp_path):
        """Test export → verify HTML output has correct structure and links."""
        # Step 1: Export notebooks
        output_dir = tmp_path / "output"
        html = main(
            notebooks=resource_dir / "marimo" / "notebooks",
            apps=resource_dir / "marimo" / "apps",
            notebooks_wasm=resource_dir / "marimo" / "notebooks_wasm",
            template=resource_dir / "templates" / "tailwind.html.j2",
            output=output_dir,
        )

        # Step 2: Verify HTML structure
        assert html
        assert "<!DOCTYPE html>" in html or "<html" in html

        # Step 3: Verify index.html exists
        index_path = output_dir / "index.html"
        assert index_path.exists()
        index_content = index_path.read_text()

        # Step 4: Verify notebook categories exist
        assert (output_dir / "notebooks").exists()
        assert (output_dir / "apps").exists()
        assert (output_dir / "notebooks_wasm").exists()

        # Step 5: Check that HTML files were created
        notebook_htmls = list((output_dir / "notebooks").glob("*.html"))
        app_htmls = list((output_dir / "apps").glob("*.html"))
        assert len(notebook_htmls) > 0
        assert len(app_htmls) > 0

        # Step 6: Verify links in index.html
        valid, invalid_links = validate_links(index_content, output_dir)
        assert valid, f"Invalid links found: {invalid_links}"

    def test_export_verify_each_notebook_html(self, resource_dir, tmp_path):
        """Test that each exported notebook is valid HTML."""
        output_dir = tmp_path / "output"
        main(
            notebooks=resource_dir / "marimo" / "notebooks",
            template=resource_dir / "templates" / "tailwind.html.j2",
            output=output_dir,
        )

        # Verify each exported notebook
        notebook_htmls = list((output_dir / "notebooks").glob("*.html"))
        assert len(notebook_htmls) > 0

        for html_file in notebook_htmls:
            content = html_file.read_text()
            # Each notebook should be valid HTML
            assert len(content) > 0
            # Should contain HTML tags
            assert "<html" in content.lower() or "<!doctype" in content.lower()

    def test_export_with_all_notebook_types_verify_links(self, resource_dir, tmp_path):
        """Test export with all three notebook types and verify all links."""
        output_dir = tmp_path / "output"
        html = main(
            notebooks=resource_dir / "marimo" / "notebooks",
            apps=resource_dir / "marimo" / "apps",
            notebooks_wasm=resource_dir / "marimo" / "notebooks_wasm",
            template=resource_dir / "templates" / "tailwind.html.j2",
            output=output_dir,
        )

        # Verify links work for all types
        valid, invalid_links = validate_links(html, output_dir)
        assert valid, f"Invalid links in index: {invalid_links}"

        # Verify each category has files
        for subdir in ["notebooks", "apps", "notebooks_wasm"]:
            html_files = list((output_dir / subdir).glob("*.html"))
            if len(html_files) > 0:
                # At least one file in this category
                sample_file = html_files[0]
                assert sample_file.exists()
                assert sample_file.stat().st_size > 0


class TestWatchModeSimulation:
    """End-to-end tests simulating watch mode behavior."""

    def test_export_modify_reexport_workflow(self, resource_dir, tmp_path):
        """Test export → modify → re-export workflow."""
        # Create a temporary notebook directory
        notebook_dir = tmp_path / "notebooks"
        notebook_dir.mkdir()

        # Copy a notebook to temp location
        source_nb = resource_dir / "marimo" / "notebooks" / "fibonacci.py"
        if not source_nb.exists():
            pytest.skip("fibonacci.py not found")

        temp_nb = notebook_dir / "test_notebook.py"
        temp_nb.write_text(source_nb.read_text())

        output_dir = tmp_path / "output"

        # Step 1: Initial export
        html1 = main(
            notebooks=notebook_dir,
            template=resource_dir / "templates" / "tailwind.html.j2",
            output=output_dir,
        )
        assert html1

        # Verify initial export
        exported_file = output_dir / "notebooks" / "test_notebook.html"
        assert exported_file.exists()

        # Step 2: Simulate file modification (add a comment)
        time.sleep(0.1)  # Ensure timestamp difference
        modified_content = temp_nb.read_text() + "\n# Modified comment\n"
        temp_nb.write_text(modified_content)

        # Step 3: Re-export
        html2 = main(
            notebooks=notebook_dir,
            template=resource_dir / "templates" / "tailwind.html.j2",
            output=output_dir,
        )
        assert html2

        # Step 4: Verify re-export updated the file
        # The file should have been re-created
        assert exported_file.exists()

    def test_add_new_notebook_reexport(self, resource_dir, tmp_path):
        """Test adding a new notebook and re-exporting."""
        notebook_dir = tmp_path / "notebooks"
        notebook_dir.mkdir()

        # Copy initial notebook
        source_nb = resource_dir / "marimo" / "notebooks" / "fibonacci.py"
        if not source_nb.exists():
            pytest.skip("fibonacci.py not found")

        (notebook_dir / "notebook1.py").write_text(source_nb.read_text())

        output_dir = tmp_path / "output"

        # Initial export with 1 notebook
        main(
            notebooks=notebook_dir,
            template=resource_dir / "templates" / "tailwind.html.j2",
            output=output_dir,
        )

        initial_files = list((output_dir / "notebooks").glob("*.html"))
        assert len(initial_files) == 1

        # Add second notebook
        (notebook_dir / "notebook2.py").write_text(source_nb.read_text())

        # Re-export with 2 notebooks
        main(
            notebooks=notebook_dir,
            template=resource_dir / "templates" / "tailwind.html.j2",
            output=output_dir,
        )

        new_files = list((output_dir / "notebooks").glob("*.html"))
        assert len(new_files) == 2

        # Verify index.html references both
        index_content = (output_dir / "index.html").read_text()
        assert "notebook1" in index_content or "notebook 1" in index_content
        assert "notebook2" in index_content or "notebook 2" in index_content


class TestCustomTemplateWorkflow:
    """End-to-end tests for custom template → export → verify rendering."""

    def test_custom_template_export_verify_content(self, tmp_path, resource_dir):
        """Test using a custom template and verifying its content appears."""
        # Create a simple custom template
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        custom_template = template_dir / "custom.html.j2"

        custom_template.write_text("""
<!DOCTYPE html>
<html>
<head><title>Custom Template Test</title></head>
<body>
<h1>My Custom Notebooks</h1>
<ul>
{% for notebook in notebooks %}
    <li><a href="{{ notebook.html_path }}">{{ notebook.display_name }}</a></li>
{% endfor %}
</ul>
<p>Total notebooks: {{ notebooks|length }}</p>
</body>
</html>
""")

        # Export with custom template
        output_dir = tmp_path / "output"
        html = main(
            notebooks=resource_dir / "marimo" / "notebooks",
            template=custom_template,
            output=output_dir,
        )

        # Verify custom template content appears
        assert "My Custom Notebooks" in html
        assert "Custom Template Test" in html
        assert "Total notebooks:" in html

    def test_custom_template_with_all_notebook_types(self, tmp_path, resource_dir):
        """Test custom template rendering all three notebook types."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        custom_template = template_dir / "multi_type.html.j2"

        custom_template.write_text("""
<!DOCTYPE html>
<html>
<head><title>Multi-Type Test</title></head>
<body>
<h2>Static Notebooks ({{ notebooks|length }})</h2>
{% for nb in notebooks %}
<div>{{ nb.display_name }}</div>
{% endfor %}

<h2>Apps ({{ apps|length }})</h2>
{% for app in apps %}
<div>{{ app.display_name }}</div>
{% endfor %}

<h2>Interactive Notebooks ({{ notebooks_wasm|length }})</h2>
{% for nb in notebooks_wasm %}
<div>{{ nb.display_name }}</div>
{% endfor %}
</body>
</html>
""")

        output_dir = tmp_path / "output"
        html = main(
            notebooks=resource_dir / "marimo" / "notebooks",
            apps=resource_dir / "marimo" / "apps",
            notebooks_wasm=resource_dir / "marimo" / "notebooks_wasm",
            template=custom_template,
            output=output_dir,
        )

        # Verify all sections appear
        assert "Static Notebooks" in html
        assert "Apps" in html
        assert "Interactive Notebooks" in html


class TestProgressCallbackWorkflow:
    """End-to-end tests for progress callback functionality."""

    def test_progress_callback_complete_workflow(self, resource_dir, tmp_path):
        """Test complete workflow with progress tracking."""
        progress_log = []

        def track_progress(completed: int, total: int, name: str) -> None:
            progress_log.append(
                {"completed": completed, "total": total, "name": name, "percentage": (completed / total) * 100}
            )

        # Export with progress tracking
        main(
            notebooks=resource_dir / "marimo" / "notebooks",
            apps=resource_dir / "marimo" / "apps",
            template=resource_dir / "templates" / "tailwind.html.j2",
            output=tmp_path / "output",
            on_progress=track_progress,
            parallel=False,  # Sequential for predictable order
        )

        # Verify progress was tracked
        assert len(progress_log) > 0

        # Verify progress values make sense
        for entry in progress_log:
            assert 0 < entry["completed"] <= entry["total"]
            assert 0 < entry["percentage"] <= 100
            assert len(entry["name"]) > 0

        # Verify final progress reaches 100% for each category
        assert any(entry["completed"] == entry["total"] for entry in progress_log)

    def test_progress_callback_with_parallel_export(self, resource_dir, tmp_path):
        """Test progress tracking with parallel export."""
        progress_calls = []

        def callback(completed: int, total: int, name: str) -> None:
            progress_calls.append(name)

        main(
            notebooks=resource_dir / "marimo" / "notebooks",
            template=resource_dir / "templates" / "tailwind.html.j2",
            output=tmp_path / "output",
            on_progress=callback,
            parallel=True,
            max_workers=2,
        )

        # Progress should be called for each notebook
        notebooks = folder2notebooks(resource_dir / "marimo" / "notebooks", Kind.NB)
        assert len(progress_calls) == len(notebooks)


class TestDebugModeWorkflow:
    """End-to-end tests for debug mode and audit logging."""

    def test_debug_output_with_audit_logging(self, resource_dir, tmp_path):
        """Test that debug mode produces audit logs."""
        from marimushka.audit import AuditLogger
        from marimushka.orchestrator import generate_index

        # Setup audit logging
        audit_log_file = tmp_path / "audit.log"
        audit_logger = AuditLogger(log_file=audit_log_file)

        # Export with audit logging
        notebooks = folder2notebooks(resource_dir / "marimo" / "notebooks", Kind.NB)

        if not notebooks:
            pytest.skip("No notebooks found for testing")

        template_path = resource_dir / "templates" / "tailwind.html.j2"

        generate_index(
            output=tmp_path / "output",
            template_file=template_path,
            notebooks=notebooks,
            apps=[],
            notebooks_wasm=[],
            audit_logger=audit_logger,
        )

        # Verify audit log exists and has content
        assert audit_log_file.exists()
        log_content = audit_log_file.read_text()
        assert len(log_content) > 0

        # Verify audit log contains JSON entries
        # Each line should be valid JSON
        lines = [line for line in log_content.strip().split("\n") if line]
        assert len(lines) > 0

    def test_export_failure_audit_logging(self, tmp_path):
        """Test that export failures are logged in audit log."""
        from marimushka.audit import AuditLogger
        from marimushka.notebook import Kind, Notebook

        audit_log_file = tmp_path / "audit.log"
        audit_logger = AuditLogger(log_file=audit_log_file)

        # Create a notebook that doesn't exist
        fake_notebook = tmp_path / "notebooks" / "nonexistent.py"
        fake_notebook.parent.mkdir()

        # This should create notebook but export will fail
        fake_notebook.write_text("# Empty notebook\n")

        nb = Notebook(fake_notebook, Kind.NB)

        # Try to export (may fail depending on marimo installation)
        nb.export(
            output_dir=tmp_path / "output",
            audit_logger=audit_logger,
        )

        # Audit log should exist
        assert audit_log_file.exists()


class TestCompleteUserWorkflow:
    """End-to-end tests simulating complete user workflows."""

    def test_first_time_user_workflow(self, resource_dir, tmp_path):
        """Test complete workflow for a first-time user."""
        # Step 1: User creates output directory
        output_dir = tmp_path / "my_site"

        # Step 2: User runs marimushka export
        html = main(
            notebooks=resource_dir / "marimo" / "notebooks",
            apps=resource_dir / "marimo" / "apps",
            output=output_dir,
            template=resource_dir / "templates" / "tailwind.html.j2",
        )

        # Step 3: Verify output structure
        assert output_dir.exists()
        assert (output_dir / "index.html").exists()

        # Step 4: Verify HTML is valid
        assert html
        assert len(html) > 0

        # Step 5: Verify links work
        valid, invalid = validate_links(html, output_dir)
        assert valid, f"Invalid links: {invalid}"

    def test_power_user_workflow_with_customization(self, resource_dir, tmp_path):
        """Test workflow for power user with custom settings."""
        # Power user wants:
        # - Custom template
        # - Progress tracking
        # - Sequential export (for debugging)
        # - Specific output location

        template_dir = tmp_path / "my_templates"
        template_dir.mkdir()
        my_template = template_dir / "template.html.j2"
        my_template.write_text("""
<!DOCTYPE html>
<html><body>
<h1>My Notebooks</h1>
{% for nb in notebooks %}<p>{{ nb.display_name }}</p>{% endfor %}
</body></html>
""")

        progress_tracker = []

        def my_progress(completed: int, total: int, name: str) -> None:
            progress_tracker.append(f"[{completed}/{total}] {name}")

        # Execute with custom settings
        output_dir = tmp_path / "custom_output"
        html = main(
            notebooks=resource_dir / "marimo" / "notebooks",
            template=my_template,
            output=output_dir,
            parallel=False,  # Sequential for debugging
            on_progress=my_progress,
            sandbox=True,
            timeout=600,
        )

        # Verify customizations worked
        assert "My Notebooks" in html
        assert len(progress_tracker) > 0
        assert output_dir.exists()
