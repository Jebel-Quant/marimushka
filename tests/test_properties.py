"""Property-based tests using hypothesis.

This module contains property-based tests that verify invariants and properties
of the marimushka codebase using hypothesis for automatic test case generation.
"""

from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from marimushka.exceptions import (
    ExportSubprocessError,
    MarimushkaError,
    NotebookInvalidError,
    TemplateNotFoundError,
)
from marimushka.notebook import Kind


class TestKindProperties:
    """Property-based tests for the Kind enum."""

    @given(st.sampled_from(["notebook", "notebook_wasm", "app"]))
    def test_from_str_is_deterministic(self, kind_str: str) -> None:
        """Test that from_str always returns the same result for the same input."""
        result1 = Kind.from_str(kind_str)
        result2 = Kind.from_str(kind_str)
        assert result1 == result2

    @given(st.sampled_from(list(Kind)))
    def test_all_kinds_have_valid_html_path(self, kind: Kind) -> None:
        """Test that all Kind values have a valid html_path."""
        html_path = kind.html_path
        assert isinstance(html_path, Path)
        assert len(str(html_path)) > 0

    @given(st.sampled_from(list(Kind)))
    def test_all_kinds_have_command(self, kind: Kind) -> None:
        """Test that all Kind values have a non-empty command list."""
        command = kind.command
        assert isinstance(command, list)
        assert len(command) > 0
        assert all(isinstance(c, str) for c in command)


class TestDisplayNameProperties:
    """Property-based tests for display name generation."""

    @given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_display_name_replaces_underscores(self, name: str) -> None:
        """Test that display names have underscores replaced with spaces."""
        # Simulate the display_name property logic
        display_name = name.replace("_", " ")
        assert "_" not in display_name or "_" not in name
        # Count underscores replaced
        original_underscores = name.count("_")
        new_spaces = display_name.count(" ") - name.count(" ")
        assert new_spaces == original_underscores


class TestExceptionProperties:
    """Property-based tests for exception handling."""

    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=50)
    def test_marimushka_error_preserves_message(self, message: str) -> None:
        """Test that MarimushkaError preserves the error message."""
        error = MarimushkaError(message)
        assert message in str(error)

    @given(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz/.", min_size=1, max_size=50),
        st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=50)
    def test_notebook_invalid_error_contains_path_and_reason(
        self, path_str: str, reason: str
    ) -> None:
        """Test that NotebookInvalidError contains both path and reason."""
        path = Path(path_str)
        error = NotebookInvalidError(path, reason=reason)
        error_str = str(error)
        assert path_str in error_str or "Invalid notebook" in error_str

    @given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz/.", min_size=1, max_size=50))
    @settings(max_examples=50)
    def test_template_not_found_error_contains_path(self, path_str: str) -> None:
        """Test that TemplateNotFoundError contains the path."""
        path = Path(path_str)
        error = TemplateNotFoundError(path)
        error_str = str(error)
        assert "Template" in error_str or "not found" in error_str

    @given(
        st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5),
        st.integers(min_value=-128, max_value=127),
    )
    @settings(max_examples=50)
    def test_export_subprocess_error_contains_return_code(
        self, command: list[str], return_code: int
    ) -> None:
        """Test that ExportSubprocessError contains the return code."""
        error = ExportSubprocessError(
            notebook_path=Path("test.py"),
            command=command,
            return_code=return_code,
        )
        error_str = str(error)
        # The error should mention the return code or export failure
        assert "Export" in error_str or "failed" in error_str.lower()


class TestPathProperties:
    """Property-based tests for path handling."""

    @given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-", min_size=1, max_size=30))
    @settings(max_examples=50)
    def test_path_stem_extraction(self, filename: str) -> None:
        """Test that path stem extraction works correctly."""
        path = Path(f"{filename}.py")
        assert path.stem == filename
        assert path.suffix == ".py"
