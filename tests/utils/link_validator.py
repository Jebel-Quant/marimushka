"""Link validation utilities for marimushka.

This module provides functions to extract and validate links from HTML content.
"""

from pathlib import Path

from bs4 import BeautifulSoup


def extract_links(html_content: str) -> dict[str, list[str]]:
    """Extract all links from HTML content.

    Args:
        html_content (str): The HTML content to extract links from.

    Returns:
        Dict[str, List[str]]: A dictionary with link types as keys and lists of links as values.
            The link types are 'internal', 'external', and 'image'.

    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Extract links from <a> tags
    links = {"internal": [], "external": [], "image": []}

    # Extract links from <a> tags
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.startswith(("http://", "https://", "//")):
            links["external"].append(href)
        else:
            links["internal"].append(href)

    # Extract links from <img> tags
    for img_tag in soup.find_all("img", src=True):
        src = img_tag["src"]
        links["image"].append(src)

    return links


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
