"""Tests for the link_validator module."""

from tests.utils.link_validator import extract_links, validate_internal_links, validate_links


class TestExtractLinks:
    """Tests for the extract_links function."""

    def test_extract_links_empty(self):
        """Test extracting links from empty HTML."""
        html_content = ""
        links = extract_links(html_content)

        assert links == {"internal": [], "external": [], "image": []}

    def test_extract_links_no_links(self):
        """Test extracting links from HTML with no links."""
        html_content = "<html><body><p>No links here</p></body></html>"
        links = extract_links(html_content)

        assert links == {"internal": [], "external": [], "image": []}

    def test_extract_links_internal(self):
        """Test extracting internal links."""
        html_content = """
        <html>
            <body>
                <a href="notebooks/test.html">Test</a>
                <a href="apps/app.html">App</a>
            </body>
        </html>
        """
        links = extract_links(html_content)

        assert set(links["internal"]) == {"notebooks/test.html", "apps/app.html"}
        assert links["external"] == []
        assert links["image"] == []

    def test_extract_links_external(self):
        """Test extracting external links."""
        html_content = """
        <html>
            <body>
                <a href="https://example.com">Example</a>
                <a href="http://test.com">Test</a>
                <a href="//cdn.example.com">CDN</a>
            </body>
        </html>
        """
        links = extract_links(html_content)

        assert links["internal"] == []
        assert set(links["external"]) == {"https://example.com", "http://test.com", "//cdn.example.com"}
        assert links["image"] == []

    def test_extract_links_images(self):
        """Test extracting image links."""
        html_content = """
        <html>
            <body>
                <img src="image.jpg" alt="Image">
                <img src="https://example.com/image.png" alt="External Image">
            </body>
        </html>
        """
        links = extract_links(html_content)

        assert links["internal"] == []
        assert links["external"] == []
        assert set(links["image"]) == {"image.jpg", "https://example.com/image.png"}

    def test_extract_links_mixed(self):
        """Test extracting mixed links."""
        html_content = """
        <html>
            <body>
                <a href="notebooks/test.html">Test</a>
                <a href="https://example.com">Example</a>
                <img src="image.jpg" alt="Image">
            </body>
        </html>
        """
        links = extract_links(html_content)

        assert links["internal"] == ["notebooks/test.html"]
        assert links["external"] == ["https://example.com"]
        assert links["image"] == ["image.jpg"]


class TestValidateInternalLinks:
    """Tests for the validate_internal_links function."""

    def test_validate_internal_links_empty(self, tmp_path):
        """Test validating empty list of internal links."""
        links = []
        valid, invalid = validate_internal_links(links, tmp_path)

        assert valid is True
        assert invalid == set()

    def test_validate_internal_links_valid(self, tmp_path):
        """Test validating valid internal links."""
        # Create test files
        notebooks_dir = tmp_path / "notebooks"
        notebooks_dir.mkdir()
        test_file = notebooks_dir / "test.html"
        test_file.write_text("Test content")

        links = ["notebooks/test.html"]
        valid, invalid = validate_internal_links(links, tmp_path)

        assert valid is True
        assert invalid == set()

    def test_validate_internal_links_invalid(self, tmp_path):
        """Test validating invalid internal links."""
        links = ["notebooks/nonexistent.html"]
        valid, invalid = validate_internal_links(links, tmp_path)

        assert valid is False
        assert invalid == {"notebooks/nonexistent.html"}

    def test_validate_internal_links_mixed(self, tmp_path):
        """Test validating mixed valid and invalid internal links."""
        # Create test files
        notebooks_dir = tmp_path / "notebooks"
        notebooks_dir.mkdir()
        test_file = notebooks_dir / "test.html"
        test_file.write_text("Test content")

        links = ["notebooks/test.html", "notebooks/nonexistent.html"]
        valid, invalid = validate_internal_links(links, tmp_path)

        assert valid is False
        assert invalid == {"notebooks/nonexistent.html"}


class TestValidateLinks:
    """Tests for the validate_links function."""

    def test_validate_links_empty(self, tmp_path):
        """Test validating links in empty HTML."""
        html_content = ""
        valid, invalid = validate_links(html_content, tmp_path)

        assert valid is True
        assert invalid == {"internal": set(), "external": set(), "image": set()}

    def test_validate_links_valid(self, tmp_path):
        """Test validating links in HTML with valid links."""
        # Create test files
        notebooks_dir = tmp_path / "notebooks"
        notebooks_dir.mkdir()
        test_file = notebooks_dir / "test.html"
        test_file.write_text("Test content")

        html_content = """
        <html>
            <body>
                <a href="notebooks/test.html">Test</a>
                <a href="https://example.com">Example</a>
                <img src="https://example.com/image.png" alt="External Image">
            </body>
        </html>
        """
        valid, invalid = validate_links(html_content, tmp_path)

        assert valid is True
        assert invalid == {"internal": set(), "external": set(), "image": set()}

    def test_validate_links_invalid(self, tmp_path):
        """Test validating links in HTML with invalid links."""
        html_content = """
        <html>
            <body>
                <a href="notebooks/nonexistent.html">Test</a>
            </body>
        </html>
        """
        valid, invalid = validate_links(html_content, tmp_path)

        assert valid is False
        assert invalid == {"internal": {"notebooks/nonexistent.html"}, "external": set(), "image": set()}

    def test_validate_links_mixed(self, tmp_path):
        """Test validating links in HTML with mixed valid and invalid links."""
        # Create test files
        notebooks_dir = tmp_path / "notebooks"
        notebooks_dir.mkdir()
        test_file = notebooks_dir / "test.html"
        test_file.write_text("Test content")

        html_content = """
        <html>
            <body>
                <a href="notebooks/test.html">Test</a>
                <a href="notebooks/nonexistent.html">Nonexistent</a>
                <a href="https://example.com">Example</a>
                <img src="https://example.com/image.png" alt="External Image">
            </body>
        </html>
        """
        valid, invalid = validate_links(html_content, tmp_path)

        assert valid is False
        assert invalid == {"internal": {"notebooks/nonexistent.html"}, "external": set(), "image": set()}
