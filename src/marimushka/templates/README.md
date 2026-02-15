# Marimushka Templates

This directory contains the HTML templates used by Marimushka to generate the index
page for exported marimo notebooks.

## Available Templates

### tailwind.html.j2

A lean template based on [Tailwind CSS](https://tailwindcss.com/).
This template uses Tailwind's utility
classes for styling, resulting in a modern, responsive design.
The Tailwind CSS is loaded via CDN, so no additional installation is required.

## Security Features

### Subresource Integrity (SRI)

All CDN resources in the templates use Subresource Integrity (SRI) hashes to ensure
that the resources loaded from CDN have not been tampered with. This protects against
supply chain attacks and CDN compromises.

**Example:**
```html
<script src="https://cdn.tailwindcss.com" 
        integrity="sha384-3hzR1LPXnJXuQpMFqYlPR4hZjbphRCkXWPMB5vzRV7rLKqHa1vW+RNa3f4aGdvPC" 
        crossorigin="anonymous"></script>
```

**Note:** SRI hashes need to be updated when the CDN resource changes. You can generate
new hashes using online tools or the `openssl` command:

```bash
curl -s https://cdn.example.com/resource.js | openssl dgst -sha384 -binary | openssl base64 -A
```

### Content Security Policy

When deploying to production, consider adding a Content Security Policy (CSP) header
to further restrict resource loading:

```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; script-src 'self' https://cdn.tailwindcss.com; style-src 'self' 'unsafe-inline'; img-src 'self' https://raw.githubusercontent.com;">
```

## Using a Custom Template

You can specify which template to use when running Marimushka:

### Command Line

```bash
# Use the default template (default)
marimushka export

# Use the Tailwind template
marimushka export --template /path/to/marimushka/templates/tailwind.html.j2
```

### Python API

```python
from marimushka.export import main
from pathlib import Path

# Use the default template (default)
main()

# Use the Tailwind template
main(template=Path(__file__).parent / "templates" / "tailwind.html.j2")
```

## Creating Your Own Template

You can create your own custom template by using the existing templates
as a reference. The template should be a Jinja2 template
file with the `.html.j2` extension.

The template has access to the following variables:

- `notebooks`: List of Notebook objects for HTML notebooks
- `notebooks_wasm`: List of Notebook objects for WebAssembly notebooks
- `apps`: List of Notebook objects for apps

Each Notebook object has the following properties:

- `display_name`: The display name of the notebook
- `html_path`: The path to the exported HTML file

## Template Security Best Practices

When creating custom templates:

1. **Always use SRI hashes** for external CDN resources
2. **Use `crossorigin="anonymous"`** for CDN resources
3. **Avoid inline scripts** where possible (use CSP-compatible patterns)
4. **Sanitize any user-provided data** (though templates don't accept user input)
5. **Keep dependencies minimal** to reduce attack surface
6. **Use HTTPS URLs only** for all external resources
