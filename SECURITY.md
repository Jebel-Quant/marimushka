# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :x:                |
| < 0.1   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Marimushka, please report it responsibly:

1. **Do not** open a public GitHub issue for security vulnerabilities
2. Email the maintainers at [contact@jqr.ae](mailto:contact@jqr.ae) with:
   - A description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact assessment
   - Any suggested fixes (optional)

## Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 7 days
- **Resolution target**: Within 30 days for critical issues

## Security Considerations

### Subprocess Execution

Marimushka executes `uvx marimo export` as a subprocess. The tool:
- Only processes `.py` files from specified directories
- Does not execute arbitrary user input as shell commands
- Uses `subprocess.run()` with explicit argument lists (no shell=True)

### Sandbox Mode

By default, notebooks are exported with `--sandbox` flag, which:
- Runs exports in an isolated environment
- Prevents access to the local filesystem beyond the notebook
- Requires dependencies to be declared in the notebook metadata

To maintain security, avoid using `--no-sandbox` in production CI/CD pipelines unless necessary.

### Template Rendering

Jinja2 templates are rendered with `autoescape` enabled for HTML/XML content, mitigating XSS risks in generated index pages.

## Security Updates

Security patches are released as part of regular version updates. Subscribe to GitHub releases to stay informed.
