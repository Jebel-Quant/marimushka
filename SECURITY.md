# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
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

Marimushka executes `uvx marimo export` as a subprocess with the following security measures:

- **Timeout Protection**: All subprocess calls have a configurable timeout (default: 300 seconds) to prevent indefinite hangs
- **Path Validation**: Input paths are validated to prevent path traversal attacks
- **Explicit Arguments**: Uses `subprocess.run()` with explicit argument lists (no shell=True)
- **Restricted Input**: Only processes `.py` files from specified directories
- **No Arbitrary Execution**: Does not execute arbitrary user input as shell commands

### Binary Path Validation

When using the `--bin-path` option to specify a custom directory for the `uvx` executable:

- **Existence Check**: Validates that the path exists and is a directory
- **Path Resolution**: Resolves paths to absolute form to prevent path traversal
- **Optional Whitelist**: Supports whitelisting specific bin paths for additional security

### Path Traversal Protection

All file and directory paths are validated before use:

- **Symlink Resolution**: Paths are resolved to their absolute form, following symlinks
- **Base Directory Validation**: Paths are checked to ensure they don't escape designated base directories
- **Template Path Validation**: Template paths are validated before loading to prevent path traversal

### Parallel Export Limits

The `--max-workers` parameter is bounded to prevent resource exhaustion:

- **Minimum**: 1 worker
- **Maximum**: 16 workers (default: 4)
- **Automatic Clamping**: Values outside this range are automatically adjusted

### Sandbox Mode

By default, notebooks are exported with `--sandbox` flag, which:
- Runs exports in an isolated environment
- Prevents access to the local filesystem beyond the notebook
- Requires dependencies to be declared in the notebook metadata

To maintain security, avoid using `--no-sandbox` in production CI/CD pipelines unless necessary.

### Template Rendering

Jinja2 templates are rendered with enhanced security:

- **Sandboxed Environment**: Uses `jinja2.sandbox.SandboxedEnvironment` to prevent code execution in templates
- **Autoescape Enabled**: HTML/XML content is automatically escaped, mitigating XSS risks
- **Path Validation**: Template paths are validated before loading

## Security Features

### Version 0.3.x+

- Path traversal protection for all file operations
- Subprocess timeout enforcement (300 seconds default)
- Binary path validation and whitelisting support
- Worker count bounds enforcement (1-16)
- Sandboxed Jinja2 template rendering
- Comprehensive input validation

## Security Best Practices

When using Marimushka:

1. **Always use sandbox mode** in production environments
2. **Limit worker count** to prevent resource exhaustion (use default or lower)
3. **Validate input paths** when integrating with other systems
4. **Review templates** before using custom templates from untrusted sources
5. **Set appropriate timeouts** for long-running notebook exports
6. **Use whitelisted bin paths** in shared/multi-tenant environments

## Security Updates

Security patches are released as part of regular version updates. Subscribe to GitHub releases to stay informed.
