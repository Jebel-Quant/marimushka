"""Tests for the exceptions.py module.

This module contains tests for the custom exception hierarchy and result types.
"""

from pathlib import Path

import pytest

from marimushka.exceptions import (
    BatchExportResult,
    ExportError,
    ExportExecutableNotFoundError,
    ExportSubprocessError,
    IndexWriteError,
    MarimushkaError,
    NotebookError,
    NotebookExportResult,
    NotebookInvalidError,
    NotebookNotFoundError,
    OutputError,
    TemplateError,
    TemplateInvalidError,
    TemplateNotFoundError,
    TemplateRenderError,
)


class TestExceptionHierarchy:
    """Tests for the exception hierarchy."""

    def test_marimushka_error_is_base(self):
        """Test that MarimushkaError is the base for all exceptions."""
        assert issubclass(TemplateError, MarimushkaError)
        assert issubclass(NotebookError, MarimushkaError)
        assert issubclass(ExportError, MarimushkaError)
        assert issubclass(OutputError, MarimushkaError)

    def test_template_error_hierarchy(self):
        """Test template error hierarchy."""
        assert issubclass(TemplateNotFoundError, TemplateError)
        assert issubclass(TemplateInvalidError, TemplateError)
        assert issubclass(TemplateRenderError, TemplateError)

    def test_notebook_error_hierarchy(self):
        """Test notebook error hierarchy."""
        assert issubclass(NotebookNotFoundError, NotebookError)
        assert issubclass(NotebookInvalidError, NotebookError)

    def test_export_error_hierarchy(self):
        """Test export error hierarchy."""
        assert issubclass(ExportExecutableNotFoundError, ExportError)
        assert issubclass(ExportSubprocessError, ExportError)

    def test_output_error_hierarchy(self):
        """Test output error hierarchy."""
        assert issubclass(IndexWriteError, OutputError)


class TestMarimushkaError:
    """Tests for MarimushkaError."""

    def test_message_attribute(self):
        """Test that message attribute is set."""
        error = MarimushkaError("test message")
        assert error.message == "test message"
        assert str(error) == "test message"

    def test_can_be_caught_as_exception(self):
        """Test that MarimushkaError can be caught as Exception."""
        with pytest.raises(Exception):  # noqa: B017, PT011
            raise MarimushkaError("test")


class TestTemplateNotFoundError:
    """Tests for TemplateNotFoundError."""

    def test_attributes(self):
        """Test that attributes are set correctly."""
        path = Path("/some/template.j2")
        error = TemplateNotFoundError(path)
        assert error.template_path == path
        assert "not found" in str(error).lower()
        assert str(path) in str(error)

    def test_can_catch_as_template_error(self):
        """Test that it can be caught as TemplateError."""
        with pytest.raises(TemplateError):
            raise TemplateNotFoundError(Path("/test.j2"))


class TestTemplateInvalidError:
    """Tests for TemplateInvalidError."""

    def test_attributes(self):
        """Test that attributes are set correctly."""
        path = Path("/some/template.j2")
        error = TemplateInvalidError(path, reason="not a file")
        assert error.template_path == path
        assert error.reason == "not a file"
        assert "not a file" in str(error)

    def test_default_reason(self):
        """Test default reason."""
        path = Path("/test.j2")
        error = TemplateInvalidError(path)
        assert error.reason == "not a file"


class TestTemplateRenderError:
    """Tests for TemplateRenderError."""

    def test_attributes(self):
        """Test that attributes are set correctly."""
        path = Path("/template.j2")
        original = ValueError("syntax error")
        error = TemplateRenderError(path, original)
        assert error.template_path == path
        assert error.original_error is original
        assert "render" in str(error).lower()


class TestNotebookNotFoundError:
    """Tests for NotebookNotFoundError."""

    def test_attributes(self):
        """Test that attributes are set correctly."""
        path = Path("/notebook.py")
        error = NotebookNotFoundError(path)
        assert error.notebook_path == path
        assert "not found" in str(error).lower()


class TestNotebookInvalidError:
    """Tests for NotebookInvalidError."""

    def test_attributes(self):
        """Test that attributes are set correctly."""
        path = Path("/notebook.txt")
        error = NotebookInvalidError(path, reason="not a Python file")
        assert error.notebook_path == path
        assert error.reason == "not a Python file"
        assert "not a Python file" in str(error)


class TestExportExecutableNotFoundError:
    """Tests for ExportExecutableNotFoundError."""

    def test_without_search_path(self):
        """Test error without search path."""
        error = ExportExecutableNotFoundError("uvx")
        assert error.executable == "uvx"
        assert error.search_path is None
        assert "PATH" in str(error)

    def test_with_search_path(self):
        """Test error with search path."""
        path = Path("/custom/bin")
        error = ExportExecutableNotFoundError("uvx", path)
        assert error.executable == "uvx"
        assert error.search_path == path
        assert str(path) in str(error)


class TestExportSubprocessError:
    """Tests for ExportSubprocessError."""

    def test_attributes(self):
        """Test that all attributes are set correctly."""
        path = Path("/notebook.py")
        cmd = ["uvx", "marimo", "export"]
        error = ExportSubprocessError(
            notebook_path=path,
            command=cmd,
            return_code=1,
            stdout="output",
            stderr="error message",
        )
        assert error.notebook_path == path
        assert error.command == cmd
        assert error.return_code == 1
        assert error.stdout == "output"
        assert error.stderr == "error message"
        assert "exit code 1" in str(error)
        assert "error message" in str(error)

    def test_stderr_truncation(self):
        """Test that long stderr is truncated in message."""
        long_stderr = "x" * 500
        error = ExportSubprocessError(
            notebook_path=Path("/nb.py"),
            command=["cmd"],
            return_code=1,
            stderr=long_stderr,
        )
        # Full stderr is preserved in attribute
        assert len(error.stderr) == 500
        # But message is truncated
        assert len(str(error)) < 500


class TestIndexWriteError:
    """Tests for IndexWriteError."""

    def test_attributes(self):
        """Test that attributes are set correctly."""
        path = Path("/output/index.html")
        original = OSError("disk full")
        error = IndexWriteError(path, original)
        assert error.index_path == path
        assert error.original_error is original
        assert "disk full" in str(error)


class TestNotebookExportResult:
    """Tests for NotebookExportResult."""

    def test_succeeded_factory(self):
        """Test the succeeded factory method."""
        nb_path = Path("/notebook.py")
        out_path = Path("/output/notebook.html")
        result = NotebookExportResult.succeeded(nb_path, out_path)

        assert result.notebook_path == nb_path
        assert result.output_path == out_path
        assert result.success is True
        assert result.error is None

    def test_failed_factory(self):
        """Test the failed factory method."""
        nb_path = Path("/notebook.py")
        error = ExportSubprocessError(nb_path, ["cmd"], 1)
        result = NotebookExportResult.failed(nb_path, error)

        assert result.notebook_path == nb_path
        assert result.output_path is None
        assert result.success is False
        assert result.error is error

    def test_immutability(self):
        """Test that result is immutable."""
        result = NotebookExportResult.succeeded(Path("/nb.py"), Path("/out.html"))
        with pytest.raises(AttributeError):
            result.success = False


class TestBatchExportResult:
    """Tests for BatchExportResult."""

    def test_empty_batch(self):
        """Test empty batch result."""
        batch = BatchExportResult()
        assert batch.total == 0
        assert batch.succeeded == 0
        assert batch.failed == 0
        assert batch.all_succeeded is True
        assert batch.failures == []
        assert batch.successes == []

    def test_add_results(self):
        """Test adding results to batch."""
        batch = BatchExportResult()

        success = NotebookExportResult.succeeded(Path("/nb1.py"), Path("/out1.html"))
        failure = NotebookExportResult.failed(Path("/nb2.py"), ExportSubprocessError(Path("/nb2.py"), ["cmd"], 1))

        batch.add(success)
        batch.add(failure)

        assert batch.total == 2
        assert batch.succeeded == 1
        assert batch.failed == 1
        assert batch.all_succeeded is False

    def test_failures_and_successes(self):
        """Test failures and successes properties."""
        batch = BatchExportResult()

        s1 = NotebookExportResult.succeeded(Path("/nb1.py"), Path("/out1.html"))
        s2 = NotebookExportResult.succeeded(Path("/nb2.py"), Path("/out2.html"))
        f1 = NotebookExportResult.failed(Path("/nb3.py"), ExportSubprocessError(Path("/nb3.py"), ["cmd"], 1))

        batch.add(s1)
        batch.add(s2)
        batch.add(f1)

        assert len(batch.successes) == 2
        assert len(batch.failures) == 1
        assert s1 in batch.successes
        assert s2 in batch.successes
        assert f1 in batch.failures

    def test_all_succeeded_true(self):
        """Test all_succeeded when all exports succeed."""
        batch = BatchExportResult()
        batch.add(NotebookExportResult.succeeded(Path("/nb1.py"), Path("/out1.html")))
        batch.add(NotebookExportResult.succeeded(Path("/nb2.py"), Path("/out2.html")))

        assert batch.all_succeeded is True

    def test_all_succeeded_false(self):
        """Test all_succeeded when some exports fail."""
        batch = BatchExportResult()
        batch.add(NotebookExportResult.succeeded(Path("/nb1.py"), Path("/out1.html")))
        batch.add(NotebookExportResult.failed(Path("/nb2.py"), ExportSubprocessError(Path("/nb2.py"), ["cmd"], 1)))

        assert batch.all_succeeded is False


class TestExceptionCatching:
    """Tests for exception catching patterns."""

    def test_catch_all_marimushka_errors(self):
        """Test catching all marimushka errors with base class."""
        errors = [
            TemplateNotFoundError(Path("/t.j2")),
            NotebookNotFoundError(Path("/n.py")),
            ExportExecutableNotFoundError("uvx"),
            IndexWriteError(Path("/i.html"), OSError()),
        ]

        for error in errors:
            with pytest.raises(MarimushkaError):
                raise error

    def test_catch_specific_error_types(self):
        """Test catching specific error types."""
        # Can catch template errors specifically
        with pytest.raises(TemplateError):
            raise TemplateNotFoundError(Path("/t.j2"))

        # Can catch notebook errors specifically
        with pytest.raises(NotebookError):
            raise NotebookInvalidError(Path("/n.txt"), "wrong extension")

        # Can catch export errors specifically
        with pytest.raises(ExportError):
            raise ExportSubprocessError(Path("/n.py"), ["cmd"], 1)
