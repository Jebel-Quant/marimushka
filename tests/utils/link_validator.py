"""Link validation utilities for marimushka.

This module provides functions to extract and validate links from HTML content.
"""

from html.parser import HTMLParser
from pathlib import Path


class LinkExtractor(HTMLParser):
    """HTML parser to extract links and image sources."""

    def __init__(self) -> None:
        """Initialize the link extractor."""
        super().__init__()
        self.links: dict[str, list[str]] = {"internal": [], "external": [], "image": []}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Handle start tags to extract links.

        Args:
            tag: The HTML tag name.
            attrs: List of (attribute, value) tuples.

        """
        attrs_dict = dict(attrs)

        # Extract links from <a> tags
        if tag == "a" and "href" in attrs_dict:
            href = attrs_dict["href"]
            if href and href.startswith(("http://", "https://", "//")):
                self.links["external"].append(href)
            elif href:
                self.links["internal"].append(href)

        # Extract links from <img> tags
        elif tag == "img" and "src" in attrs_dict:
            src = attrs_dict["src"]
            if src:
                self.links["image"].append(src)


def extract_links(html_content: str) -> dict[str, list[str]]:
    """Extract all links from HTML content.

    Args:
        html_content (str): The HTML content to extract links from.

    Returns:
        Dict[str, List[str]]: A dictionary with link types as keys and lists of links as values.
            The link types are 'internal', 'external', and 'image'.

    """
    parser = LinkExtractor()
    parser.feed(html_content)
    return parser.links


def validate_internal_links(links: list[str], output_dir: Path) -> tuple[bool, set[str]]:
    """Validate internal links by checking if the referenced files exist.

    Args:
        links (List[str]): List of internal links to validate.
        output_dir (Path): The output directory where the files should be located.

    Returns:
        Tuple[bool, Set[str]]: A tuple containing a boolean indicating if all links are valid,
            and a set of invalid links.

    """
    invalid_links = set()

    for link in links:
        # Handle relative paths
        link_path = output_dir / link

        if not link_path.exists():
            invalid_links.add(link)

    return len(invalid_links) == 0, invalid_links


def validate_links(html_content: str, output_dir: Path) -> tuple[bool, dict[str, set[str]]]:
    """Validate all links in the HTML content.

    Args:
        html_content (str): The HTML content to validate links in.
        output_dir (Path): The output directory where internal files should be located.

    Returns:
        Tuple[bool, Dict[str, Set[str]]]: A tuple containing a boolean indicating if all links are valid,
            and a dictionary with link types as keys and sets of invalid links as values.

    """
    links = extract_links(html_content)

    # Validate internal links
    internal_valid, invalid_internal = validate_internal_links(links["internal"], output_dir)

    # For now, we'll assume all external links and image links are valid
    # In a real-world scenario, you might want to check these as well

    all_valid = internal_valid
    invalid_links = {"internal": invalid_internal, "external": set(), "image": set()}

    return all_valid, invalid_links
