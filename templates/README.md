# Marimushka Templates

This directory contains HTML templates used by Marimushka to generate the index page for exported marimo notebooks. Templates use [Jinja2](https://jinja.palletsprojects.com/) syntax.

## Available Templates

### tailwind.html.j2

The default template using [Tailwind CSS](https://tailwindcss.com/) via CDN. Features:
- Responsive grid layout (1/2/3 columns based on screen size)
- Color-coded sections: blue (notebooks), green (interactive), amber (apps)
- marimo logo header
- Clean, modern design

## Template Variables

Templates receive three lists of `Notebook` objects:

| Variable | Description |
|----------|-------------|
| `notebooks` | Static HTML notebooks (non-interactive) |
| `notebooks_wasm` | Interactive WebAssembly notebooks (editable code) |
| `apps` | WebAssembly applications (hidden code) |

### Notebook Object Properties

| Property | Type | Description |
|----------|------|-------------|
| `display_name` | `str` | Human-readable name (underscores converted to spaces) |
| `html_path` | `Path` | Relative path to the exported HTML file |
| `path` | `Path` | Original `.py` file path |
| `kind` | `Kind` | Enum: `NB`, `NB_WASM`, or `APP` |

## Creating Custom Templates

### Basic Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Notebooks</title>
</head>
<body>
    {% if notebooks %}
    <section>
        <h2>Notebooks</h2>
        <ul>
        {% for nb in notebooks %}
            <li><a href="{{ nb.html_path }}">{{ nb.display_name }}</a></li>
        {% endfor %}
        </ul>
    </section>
    {% endif %}

    {% if notebooks_wasm %}
    <section>
        <h2>Interactive Notebooks</h2>
        <ul>
        {% for nb in notebooks_wasm %}
            <li><a href="{{ nb.html_path }}">{{ nb.display_name }}</a></li>
        {% endfor %}
        </ul>
    </section>
    {% endif %}

    {% if apps %}
    <section>
        <h2>Applications</h2>
        <ul>
        {% for app in apps %}
            <li><a href="{{ app.html_path }}">{{ app.display_name }}</a></li>
        {% endfor %}
        </ul>
    </section>
    {% endif %}
</body>
</html>
```

### Example: Bootstrap Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notebook Gallery</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container py-5">
        <h1 class="text-center mb-5">Notebook Gallery</h1>

        {% if notebooks %}
        <h2 class="h4 mb-3">Static Notebooks</h2>
        <div class="row g-3 mb-5">
            {% for nb in notebooks %}
            <div class="col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <h5 class="card-title">{{ nb.display_name }}</h5>
                        <a href="{{ nb.html_path }}" class="btn btn-primary">Open</a>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% if notebooks_wasm %}
        <h2 class="h4 mb-3">Interactive Notebooks</h2>
        <div class="row g-3 mb-5">
            {% for nb in notebooks_wasm %}
            <div class="col-md-4">
                <div class="card h-100 border-success">
                    <div class="card-body">
                        <h5 class="card-title">{{ nb.display_name }}</h5>
                        <span class="badge bg-success mb-2">Editable</span>
                        <a href="{{ nb.html_path }}" class="btn btn-success d-block">Open</a>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% if apps %}
        <h2 class="h4 mb-3">Applications</h2>
        <div class="row g-3">
            {% for app in apps %}
            <div class="col-md-4">
                <div class="card h-100 border-warning">
                    <div class="card-body">
                        <h5 class="card-title">{{ app.display_name }}</h5>
                        <span class="badge bg-warning text-dark mb-2">App</span>
                        <a href="{{ app.html_path }}" class="btn btn-warning d-block">Launch</a>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
</body>
</html>
```

### Example: Minimal Dark Theme

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notebooks</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui, sans-serif; background: #1a1a2e; color: #eee; padding: 2rem; }
        h1 { margin-bottom: 2rem; color: #fff; }
        h2 { margin: 1.5rem 0 1rem; color: #aaa; font-size: 0.875rem; text-transform: uppercase; }
        ul { list-style: none; display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem; }
        a { display: block; padding: 1rem; background: #16213e; color: #fff; text-decoration: none; border-radius: 8px; transition: background 0.2s; }
        a:hover { background: #0f3460; }
        .interactive a { border-left: 3px solid #4ecca3; }
        .apps a { border-left: 3px solid #ff6b6b; }
    </style>
</head>
<body>
    <h1>Notebooks</h1>

    {% if notebooks %}
    <section>
        <h2>Static</h2>
        <ul>{% for nb in notebooks %}<li><a href="{{ nb.html_path }}">{{ nb.display_name }}</a></li>{% endfor %}</ul>
    </section>
    {% endif %}

    {% if notebooks_wasm %}
    <section class="interactive">
        <h2>Interactive</h2>
        <ul>{% for nb in notebooks_wasm %}<li><a href="{{ nb.html_path }}">{{ nb.display_name }}</a></li>{% endfor %}</ul>
    </section>
    {% endif %}

    {% if apps %}
    <section class="apps">
        <h2>Apps</h2>
        <ul>{% for app in apps %}<li><a href="{{ app.html_path }}">{{ app.display_name }}</a></li>{% endfor %}</ul>
    </section>
    {% endif %}
</body>
</html>
```

## Advanced Techniques

### Conditional Rendering

```html
{# Only show section if there are items #}
{% if notebooks %}
    {# ... #}
{% endif %}

{# Show different content based on count #}
{% if notebooks | length > 10 %}
    <p>Showing {{ notebooks | length }} notebooks</p>
{% endif %}
```

### Accessing Notebook Properties

```html
{% for nb in notebooks %}
    {# Display name with spaces #}
    <h3>{{ nb.display_name }}</h3>

    {# Original filename #}
    <small>Source: {{ nb.path.name }}</small>

    {# Link to HTML #}
    <a href="{{ nb.html_path }}">Open</a>

    {# Check notebook kind #}
    {% if nb.kind.value == 'notebook' %}
        <span class="badge">Static</span>
    {% endif %}
{% endfor %}
```

### Adding Metadata

```html
{# Total counts in header #}
<p>
    {{ notebooks | length }} notebooks,
    {{ notebooks_wasm | length }} interactive,
    {{ apps | length }} apps
</p>

{# Generation timestamp (add to template context if needed) #}
<footer>Generated: {{ now() if now is defined else 'N/A' }}</footer>
```

## Using Custom Templates

### Command Line

```bash
# Use default Tailwind template
uvx marimushka export

# Use custom template
uvx marimushka export --template ./my-template.html.j2

# Use template from templates/ directory
uvx marimushka export --template templates/custom.html.j2
```

### Python API

```python
from marimushka.export import main

main(
    template="./my-template.html.j2",
    notebooks="notebooks",
    apps="apps",
    output="_site"
)
```

## Template File Location

Templates can be placed anywhere, but common locations:
- `templates/` in your project root (recommended)
- `src/marimushka/templates/` for built-in templates
- Any absolute or relative path passed to `--template`

The default template is `src/marimushka/templates/tailwind.html.j2`.
