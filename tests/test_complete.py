"""Test complete marimushka build process."""

from marimushka.export import main
from tests.utils.link_validator import validate_links


def test_complete(resource_dir, tmp_path):
    """Test complete marimushka build process."""
    # Call main function and capture the returned HTML
    html_output = main(
        notebooks=resource_dir / "notebooks",
        apps=resource_dir / "apps",
        template=resource_dir / "templates" / "default.html.j2",
        output=tmp_path / "output",
        notebooks_wasm=resource_dir / "notebooks_wasm",
    )

    # Write the HTML output to a file in the resources directory for later testing
    html_output_file = resource_dir / "html_output" / "complete_output.html"
    # html_output_file.parent.mkdir(exist_ok=True)
    # html_output_file.write_text(html_output)

    # Verify the file exists
    assert html_output_file.exists()
    assert html_output_file.read_text() == html_output

    # Validate all links in the HTML output
    valid, invalid_links = validate_links(html_output, tmp_path / "output")

    # If there are any invalid links, print them for debugging
    if not valid:
        print(f"Invalid links found: {invalid_links}")

    # Assert that all links are valid
    assert valid, f"Invalid links found: {invalid_links}"


def test_no_apps(resource_dir, tmp_path):
    """Test complete marimushka build process."""
    # Call main function and capture the returned HTML
    html_output = main(
        notebooks=resource_dir / "notebooks",
        notebooks_wasm=resource_dir / "notebooks_wasm",
        template=resource_dir / "templates" / "default.html.j2",
        output=tmp_path / "output",
    )

    # Write the HTML output to a file in the resources directory for later testing
    html_output_file = resource_dir / "html_output" / "no_apps_output.html"
    # html_output_file.parent.mkdir(exist_ok=True)
    # html_output_file.write_text(html_output)

    # Verify the file was created successfully
    assert html_output_file.exists()
    assert html_output_file.read_text() == html_output

    # Validate all links in the HTML output
    valid, invalid_links = validate_links(html_output, tmp_path / "output")

    # If there are any invalid links, print them for debugging
    if not valid:
        print(f"Invalid links found: {invalid_links}")

    # Assert that all links are valid
    assert valid, f"Invalid links found: {invalid_links}"
