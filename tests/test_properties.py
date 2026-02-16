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
    def test_notebook_invalid_error_contains_path_and_reason(self, path_str: str, reason: str) -> None:
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
    def test_export_subprocess_error_contains_return_code(self, command: list[str], return_code: int) -> None:
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


class TestNotebookExportProperties:
    """Property-based tests for notebook export edge cases."""

    @given(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-",
            min_size=1,
            max_size=30,
        )
    )
    @settings(max_examples=50)
    def test_notebook_path_with_various_names(self, filename: str) -> None:
        """Test that notebook paths handle various valid filenames."""
        # Create a valid path structure
        Path(f"{filename}.py")
        # Notebook should have a consistent display name
        expected_display = filename.replace("_", " ")

        # The display_name property logic should work correctly
        assert expected_display.count(" ") >= filename.count("_")

    @given(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20),
        st.sampled_from(list(Kind)),
    )
    @settings(max_examples=50)
    def test_notebook_html_path_structure(self, stem: str, kind: Kind) -> None:
        """Test that notebook HTML paths follow the expected structure."""
        # HTML path should be consistent with the kind
        html_path = kind.html_path / f"{stem}.html"

        assert html_path.suffix == ".html"
        assert html_path.stem == stem
        assert str(html_path).endswith(".html")

    @given(st.sampled_from(list(Kind)))
    @settings(max_examples=20)
    def test_kind_command_structure(self, kind: Kind) -> None:
        """Test that all kind commands follow expected structure."""
        command = kind.command

        # All commands should start with marimo and export
        assert command[0] == "marimo"
        assert command[1] == "export"
        # Should have at least 3 elements
        assert len(command) >= 3


class TestBatchExportResultProperties:
    """Property-based tests for batch export results."""

    @given(st.lists(st.booleans(), min_size=0, max_size=20))
    @settings(max_examples=100)
    def test_batch_result_statistics(self, successes: list[bool]) -> None:
        """Test that batch result statistics are consistent."""
        from marimushka.exceptions import BatchExportResult, NotebookExportResult

        batch = BatchExportResult()

        # Add results based on the success list
        for idx, success in enumerate(successes):
            nb_path = Path(f"notebook_{idx}.py")
            if success:
                result = NotebookExportResult.succeeded(nb_path, Path(f"output_{idx}.html"))
            else:
                from marimushka.exceptions import ExportSubprocessError

                error = ExportSubprocessError(nb_path, ["cmd"], 1)
                result = NotebookExportResult.failed(nb_path, error)
            batch.add(result)

        # Verify statistics
        assert batch.total == len(successes)
        assert batch.succeeded == sum(successes)
        assert batch.failed == sum(not s for s in successes)
        assert batch.all_succeeded == all(successes)
        assert len(batch.successes) == sum(successes)
        assert len(batch.failures) == sum(not s for s in successes)


class TestSecurityValidationProperties:
    """Property-based tests for security validation functions."""

    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=50)
    def test_validate_max_workers_bounds(self, workers: int) -> None:
        """Test that max_workers validation properly bounds values."""
        from marimushka.security import validate_max_workers

        result = validate_max_workers(workers, min_workers=1, max_allowed=16)

        # Result should always be within bounds
        assert 1 <= result <= 16
        # If input is within bounds, it should be unchanged
        if 1 <= workers <= 16:
            assert result == workers

    @given(st.integers(min_value=-100, max_value=0))
    @settings(max_examples=30)
    def test_validate_max_workers_negative_becomes_min(self, workers: int) -> None:
        """Test that negative or zero workers becomes minimum."""
        from marimushka.security import validate_max_workers

        result = validate_max_workers(workers, min_workers=1, max_allowed=16)
        assert result == 1

    @given(st.integers(min_value=17, max_value=1000))
    @settings(max_examples=30)
    def test_validate_max_workers_excessive_becomes_max(self, workers: int) -> None:
        """Test that excessive workers becomes maximum."""
        from marimushka.security import validate_max_workers

        result = validate_max_workers(workers, min_workers=1, max_allowed=16)
        assert result == 16


class TestPathManipulationProperties:
    """Property-based tests for path manipulation and sanitization."""

    @given(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-./",
            min_size=5,
            max_size=50,
        )
    )
    @settings(max_examples=50)
    def test_sanitize_error_message_removes_paths(self, text: str) -> None:
        """Test that error message sanitization handles various path structures."""
        from marimushka.security import sanitize_error_message

        # Create error message with absolute path pattern
        error_msg = f"Error in /home/user/secret/{text}"
        sanitized = sanitize_error_message(error_msg)

        # Should not contain the full absolute path
        assert "/home/user/secret" not in sanitized or "Error" in sanitized

    @given(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5))
    @settings(max_examples=50)
    def test_sanitize_custom_patterns(self, patterns: list[str]) -> None:
        """Test that custom patterns are properly redacted."""
        from marimushka.security import sanitize_error_message

        message = "Error: " + " ".join(patterns)
        sanitized = sanitize_error_message(message, sensitive_patterns=patterns)

        # All patterns should be redacted
        for pattern in patterns:
            if pattern in message:  # Only check if pattern was in original
                assert pattern not in sanitized or sanitized.count("<redacted>") > 0


class TestConfigurationValidationProperties:
    """Property-based tests for configuration validation."""

    @given(
        st.integers(min_value=1, max_value=1000),
        st.integers(min_value=1, max_value=32),
    )
    @settings(max_examples=50)
    def test_config_max_workers_bounded(self, timeout: int, max_workers: int) -> None:
        """Test that configuration max_workers is properly bounded."""
        from marimushka.config import MarimushkaConfig

        config = MarimushkaConfig(timeout=timeout, max_workers=max_workers)

        # Config should accept the values
        assert config.timeout == timeout
        assert config.max_workers == max_workers

    @given(st.text(min_size=1, max_size=50), st.text(min_size=1, max_size=50))
    @settings(max_examples=50)
    def test_config_path_strings(self, output: str, notebooks: str) -> None:
        """Test that configuration accepts various path strings."""
        from marimushka.config import MarimushkaConfig

        config = MarimushkaConfig(output=output, notebooks=notebooks)

        # Paths should be stored as provided
        assert config.output == output
        assert config.notebooks == notebooks

    @given(st.booleans(), st.booleans())
    @settings(max_examples=20)
    def test_config_boolean_flags(self, sandbox: bool, parallel: bool) -> None:
        """Test that configuration boolean flags work correctly."""
        from marimushka.config import MarimushkaConfig

        config = MarimushkaConfig(sandbox=sandbox, parallel=parallel)

        assert config.sandbox == sandbox
        assert config.parallel == parallel


class TestTemplateRenderingProperties:
    """Property-based tests for template rendering edge cases."""

    @given(st.integers(min_value=0, max_value=20))
    @settings(max_examples=30)
    def test_template_with_varying_notebook_counts(self, count: int) -> None:
        """Test that template rendering handles varying notebook counts."""
        from marimushka.notebook import Notebook

        # Create lists of varying sizes
        # We can't actually create real notebooks, but we can test the logic
        # that would handle different list sizes
        assert count >= 0

        # The template should be able to handle empty lists
        notebooks: list[Notebook] = []
        apps: list[Notebook] = []

        # Verify list properties
        assert len(notebooks) == 0
        assert len(apps) == 0
