# ADR-004: Template System Design

**Status**: Accepted

**Date**: 2025-01-18

**Deciders**: Development Team

## Context

Users need to customize the index page appearance to match their website branding. Requirements:

- Generate index pages listing all exported notebooks
- Support custom layouts and styling
- Provide notebook metadata for rendering
- Prevent security issues (code execution)
- Work with standard templating tools
- Be simple for non-programmers to customize

We needed to choose:
1. Template engine (Jinja2, Mako, Mustache, etc.)
2. Template API (what data to expose)
3. Security model (sandboxing, validation)
4. Default template design

## Decision

We chose **Jinja2 with sandboxed execution** and a clean template API:

### Template Engine: Jinja2

**Why Jinja2**:
- Industry standard in Python ecosystem
- Familiar to Django/Flask users
- Rich feature set (loops, conditionals, filters)
- Active maintenance
- Good documentation

### Template API

Templates receive three lists of `Notebook` objects:

```python
{
    "notebooks": [Notebook(path, Kind.NB), ...],     # Static HTML
    "apps": [Notebook(path, Kind.APP), ...],         # Run mode apps
    "notebooks_wasm": [Notebook(path, Kind.NB_WASM), ...]  # Interactive
}
```

Each `Notebook` exposes:
- `display_name`: Human-friendly name (underscores → spaces)
- `html_path`: Relative path to exported HTML
- `path`: Original `.py` file path
- `kind`: The notebook type (`Kind` enum)

### Security: Sandboxed Environment

```python
env = SandboxedEnvironment(
    loader=jinja2.FileSystemLoader(template_dir),
    autoescape=jinja2.select_autoescape(["html", "xml"])
)
```

Prevents:
- Code execution in templates
- Access to Python builtins
- File system access
- Import statements

### Default Template: Tailwind CSS

Provides:
- Modern, responsive design
- Dark/light mode support
- Organized sections for each notebook type
- Clean card-based layout
- Professional appearance out of the box

Located at: `src/marimushka/templates/tailwind.html.j2`

## Consequences

### Positive

1. **Familiar Technology**: Most Python developers know Jinja2
2. **Powerful**: Loops, conditionals, filters, macros available
3. **Secure**: Sandboxing prevents code execution
4. **Flexible**: Easy to customize appearance completely
5. **Clean API**: Simple notebook object with clear properties
6. **Good Defaults**: Tailwind template looks professional

### Negative

1. **Jinja2 Dependency**: Adds ~500KB to installation
2. **Learning Curve**: Non-programmers may find Jinja2 syntax unfamiliar
3. **Sandbox Limitations**: Some advanced Jinja2 features unavailable
4. **Template Debugging**: Jinja2 errors can be cryptic

## Example Template

```jinja2
<!DOCTYPE html>
<html>
<head><title>My Notebooks</title></head>
<body>
  <h1>Static Notebooks</h1>
  <ul>
  {% for notebook in notebooks %}
    <li>
      <a href="{{ notebook.html_path }}">
        {{ notebook.display_name }}
      </a>
    </li>
  {% endfor %}
  </ul>

  <h1>Apps</h1>
  <ul>
  {% for app in apps %}
    <li>
      <a href="{{ app.html_path }}">
        {{ app.display_name }}
      </a>
    </li>
  {% endfor %}
  </ul>
</body>
</html>
```

## Alternatives Considered

**Mustache/Handlebars**: Simpler but too limited
**Mako**: Powerful but less secure
**Custom DSL**: Too much work, poor compatibility
**Python string formatting**: Too limited, insecure

## Related ADRs

- [ADR-003: Security Model](ADR-003-security-model.md) - Sandboxing strategy
- [ADR-001: Module Structure](ADR-001-module-structure-refactoring.md) - Template rendering module

## Notes

Template validation ensures:
- Template file exists
- Has `.j2` or `.jinja2` extension (warning only)
- Not larger than 10MB
- No path traversal
