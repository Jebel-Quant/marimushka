<div align="center">
  
# <img src="https://raw.githubusercontent.com/Jebel-Quant/rhiza/main/.rhiza/assets/rhiza-logo.svg" alt="Rhiza Logo" width="30"> marimushka
![Synced with Rhiza](https://img.shields.io/badge/synced%20with-rhiza-2FA4A9?color=2FA4A9)

[![PyPI version](https://img.shields.io/pypi/v/marimushka.svg)](https://pypi.org/project/marimushka/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/jebel-quant/marimushka/rhiza_release.yml?label=release)](https://github.com/jebel-quant/marimushka/actions/workflows/rhiza_release.yml)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![CodeFactor](https://www.codefactor.io/repository/github/jebel-quant/marimushka/badge)](https://www.codefactor.io/repository/github/jebel-quant/marimushka)
[![Coverage](https://img.shields.io/endpoint?url=https://jebel-quant.github.io/marimushka/tests/coverage-badge.json&cacheSeconds=3600)](https://jebel-quant.github.io/marimushka/tests/html-coverage/index.html)
[![Downloads](https://static.pepy.tech/personalized-badge/marimushka?period=month&units=international_system&left_color=black&right_color=orange&left_text=PyPI%20downloads%20per%20month)](https://pepy.tech/project/marimushka)
[![GitHub stars](https://img.shields.io/github/stars/jebel-quant/marimushka)](https://github.com/jebel-quant/marimushka/stargazers)

Export [marimo](https://marimo.io) notebooks in style.

</div>


## 🚀 Overview

Marimushka is a powerful tool for exporting [marimo](https://marimo.io) notebooks
to HTML/WebAssembly format with custom styling. It helps you create beautiful,
interactive web versions of your marimo notebooks and applications that can be
shared with others or deployed to static hosting services like GitHub Pages.

Marimushka "exports" your marimo notebooks
in a stylish, customizable HTML template, making them accessible to anyone
with a web browser - no Python installation required!

### ✨ Features

- 📊 **Export marimo notebooks** (.py files) to HTML/WebAssembly format
- 🎨 **Customize the output** using Jinja2 templates
- 📱 **Support for both interactive notebooks and standalone applications**
  - Notebooks are exported in "edit" mode, allowing code modification
  - Apps are exported in "run" mode with hidden code for a clean interface
- 🌐 **Generate an index page** that lists all your notebooks and apps
- 🔄 **Integrate with GitHub Actions** for automated deployment
- 🔍 **Recursive directory scanning** to find all notebooks in a project
- 🧩 **Flexible configuration** with command-line options, Python API, and config files
- 🔒 **Security-first design** with multiple protection layers
  - Path traversal protection
  - TOCTOU race condition prevention
  - DoS protections (file size limits, timeouts, worker bounds)
  - Error message sanitization
  - Subresource Integrity (SRI) for CDN resources
  - Audit logging for security events
  - Secure file permissions

## 📋 Requirements

- Python 3.10+
- [marimo](https://marimo.io) (installed automatically as a dependency)
- [uvx](https://docs.astral.sh/uv/guides/tools/) (recommended to bypass installation)

## 📥 Installation

We do not recommend installing the tool locally. Please use

```bash
# install marimushka on the fly
uvx marimushka

# or
uvx marimushka --help
```

## 🛠️ Usage

### Command Line

```bash
# Basic usage (some help is displayed)
uvx marimushka

# Start exporting, get some help first
uvx marimushka export --help
# Do it
uvx marimushka export

# Specify a custom template
uvx marimushka export --template path/to/template.html.j2

# Specify a custom output directory
uvx marimushka export --output my_site

# Specify custom notebook and app directories
uvx marimushka export --notebooks path/to/notebooks --apps path/to/apps

# Disable sandbox mode (use project environment)
uvx marimushka export --no-sandbox
```

### Configuration File

Marimushka supports configuration via a `.marimushka.toml` file in your project root:

```toml
[marimushka]
output = "_site"
notebooks = "notebooks"
apps = "apps"
sandbox = true
parallel = true
max_workers = 4
timeout = 300

[marimushka.security]
audit_enabled = true
audit_log = ".marimushka-audit.log"
max_file_size_mb = 10
file_permissions = "0o644"
```

See `.marimushka.toml.example` in the repository for a complete example with documentation.

### Project Structure

Marimushka recommends your project to have the following structure
to be aligned with its default arguments. However, it is possible
to inject alternative locations

```bash
your-project/
├── notebooks/       # Static marimo notebooks (.py files)
├── notebooks_wasm/  # Interactive marimo notebooks (.py files)
├── apps/            # Marimo applications (.py files)
└── templates/       # Optional: Custom templates for export
    └── custom.html.j2   # Default template location
```

### Marimo Notebook Requirements

By default, marimushka exports notebooks using the `--sandbox` flag.
This ensures that the export process runs in an isolated environment, which is safer and ensures that your notebook's dependencies are correctly defined in the notebook itself (e.g. using `/// script` metadata).

When developing or testing notebooks locally, it is good practice to use the `--sandbox` flag:

```bash
# Running a notebook with the sandbox flag
marimo run your_notebook.py --sandbox

# Or with uvx
uvx marimo run your_notebook.py --sandbox
```

If you need to export notebooks that rely on the local environment (e.g. packages installed in the current venv but not declared in the notebook), you can disable the sandbox:

```bash
uvx marimushka export --no-sandbox
```

### GitHub Action

You can use marimushka in your GitHub Actions workflow to automatically export
and deploy your notebooks:

```yaml
permissions:
  contents: read

jobs:
  export:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Export marimo notebooks
        uses: jebel-quant/marimushka@v0.2.1
        with:
          template: 'path/to/template.html.j2'  # Optional: custom template
          notebooks: 'notebooks'                # Optional: notebooks directory
          apps: 'apps'                          # Optional: apps directory
          notebooks_wasm: 'notebooks'           # Optional: interactive notebooks directory
```

The action will create a GitHub artifact named 'marimushka' containing all exported files.
The artifact is available in all jobs further declaring a dependency
on the 'export' job.

#### Action Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `notebooks` | Directory containing marimo notebook files (.py) to be exported as static HTML notebooks. | No | `notebooks` |
| `apps` | Directory containing marimo app files (.py) to be exported as WebAssembly applications with hidden code (run mode). | No | `apps` |
| `notebooks_wasm` | Directory containing marimo notebook files (.py) to be exported as interactive WebAssembly notebooks with editable code (edit mode). | No | `notebooks` |
| `template` | Path to a custom Jinja2 template file (.html.j2) for the index page. If not provided, the default Tailwind CSS template will be used. | No | |

#### Example: Export and Deploy to GitHub Pages

```yaml
name: Export and Deploy

on:
  push:
    branches: [ main ]

jobs:
  export-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Export marimo notebooks
        uses: jebel-quant/marimushka@v0.2.1
        with:
          notebooks: 'notebooks'
          apps: 'apps'

      - name: Deploy to GitHub Pages
        uses: JamesIves/github-pages-deploy-action@v4
        with:
          folder: artifacts/marimushka
          branch: gh-pages
```

### Advanced CI/CD Patterns

#### GitLab CI Integration

Marimushka works seamlessly with GitLab CI/CD:

```yaml
# .gitlab-ci.yml
stages:
  - export
  - deploy

export-notebooks:
  stage: export
  image: python:3.11
  script:
    - pip install uv
    - uvx marimushka export --output public
  artifacts:
    paths:
      - public
  only:
    - main

pages:
  stage: deploy
  dependencies:
    - export-notebooks
  script:
    - echo "Deploying to GitLab Pages"
  artifacts:
    paths:
      - public
  only:
    - main
```

#### CircleCI Integration

```yaml
# .circleci/config.yml
version: 2.1

jobs:
  export:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - run:
          name: Install dependencies
          command: pip install uv
      - run:
          name: Export notebooks
          command: uvx marimushka export
      - persist_to_workspace:
          root: .
          paths:
            - _site
      - store_artifacts:
          path: _site
          destination: notebooks

workflows:
  main:
    jobs:
      - export
```

#### Netlify Integration

Deploy directly to Netlify from GitHub Actions:

```yaml
# .github/workflows/netlify.yml
name: Deploy to Netlify

on:
  push:
    branches: [main]
  pull_request:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Export notebooks
        uses: jebel-quant/marimushka@v0.2.1
      
      - name: Deploy to Netlify
        uses: nwtgck/actions-netlify@v2
        with:
          publish-dir: artifacts/marimushka
          production-branch: main
          github-token: ${{ secrets.GITHUB_TOKEN }}
          deploy-message: "Deploy from GitHub Actions"
        env:
          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}
```

#### Vercel Integration

Deploy to Vercel using GitHub Actions:

```yaml
# .github/workflows/vercel.yml
name: Deploy to Vercel

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Export notebooks
        uses: jebel-quant/marimushka@v0.2.1
      
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: artifacts/marimushka
```

#### AWS S3 + CloudFront

Deploy to AWS infrastructure:

```yaml
# .github/workflows/aws.yml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Export notebooks
        uses: jebel-quant/marimushka@v0.2.1
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Sync to S3
        run: |
          aws s3 sync artifacts/marimushka/ s3://${{ secrets.S3_BUCKET }}/notebooks/ \
            --delete \
            --cache-control "public, max-age=3600"
      
      - name: Invalidate CloudFront
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CLOUDFRONT_DIST_ID }} \
            --paths "/*"
```

**For more CI/CD recipes and patterns**, see:
- [RECIPES.md](RECIPES.md#cicd-integration) - Comprehensive recipes and examples
- [FAQ.md](FAQ.md#deployment--cicd) - Common deployment questions
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md#github-action-issues) - CI/CD troubleshooting

## 🎨 Customizing Templates

Marimushka uses Jinja2 templates to generate the 'index.html' file.
You can customize the appearance of the index page by creating your own template.

The template has access to two variables:

- `notebooks`: A list of Notebook objects representing regular notebooks
- `apps`: A list of Notebook objects representing app notebooks
- `notebooks_wasm`: A list of Notebook objects representing interactive notebooks

Each Notebook object has the following properties:

- `display_name`: The display name of the notebook (derived from the filename)
- `html_path`: The path to the exported HTML file
- `path`: The original path to the notebook file
- `kind`: The type of the notebook (notebook / apps / notebook_wasm )

Example template structure:

```html
<!DOCTYPE html>
<html>
<head>
  <title>My Marimo Notebooks</title>
  <style>
    /* Your custom CSS here */
  </style>
</head>
<body>
  <h1>My Notebooks</h1>

  {% if notebooks %}
  <h2>Interactive Notebooks</h2>
  <ul>
    {% for notebook in notebooks %}
    <li>
      <a href="{{ notebook.html_path }}">{{ notebook.display_name }}</a>
    </li>
    {% endfor %}
  </ul>
  {% endif %}

  {% if apps %}
  <h2>Applications</h2>
  <ul>
    {% for app in apps %}
    <li>
      <a href="{{ app.html_path }}">{{ app.display_name }}</a>
    </li>
    {% endfor %}
  </ul>
  {% endif %}
</body>
</html>
```

## 🔒 Security

Marimushka is designed with security as a priority. See [SECURITY.md](SECURITY.md) for details on:

- Security features and protections
- Best practices for secure deployment
- Configuration options for enhanced security
- Audit logging
- Vulnerability reporting

## 👥 Contributing

Contributions are welcome! Here's how you can contribute:

1. 🍴 Fork the repository
2. 🌿 Create your feature branch (`git checkout -b feature/amazing-feature`)
3. 💾 Commit your changes (`git commit -m 'Add some amazing feature'`)
4. 🚢 Push to the branch (`git push origin feature/amazing-feature`)
5. 🔍 Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/jebel-quant/marimushka.git
cd marimushka

# Install dependencies
make install

# Run tests
make test

# Run linting and formatting
make fmt
```

## 📚 Documentation

Marimushka has comprehensive documentation to help you get the most out of it:

### Core Documentation

- **[README.md](README.md)** - This file. Getting started guide and feature overview
- **[CHANGELOG.md](CHANGELOG.md)** - Detailed version history with migration notes
- **[MIGRATION.md](docs/MIGRATION.md)** - Version upgrade guides with code examples
- **[API.md](API.md)** - Complete Python API reference for programmatic usage

### User Guides

- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues and solutions
  - Installation problems
  - Export failures
  - Template errors
  - Performance issues
  - GitHub Action troubleshooting
  
- **[RECIPES.md](docs/RECIPES.md)** - Real-world usage patterns and examples
  - Basic workflows
  - CI/CD integration (GitHub, GitLab, CircleCI)
  - Custom templates
  - Advanced patterns
  - Deployment strategies
  
- **[FAQ.md](docs/FAQ.md)** - Frequently asked questions
  - Quick answers to 50+ common questions
  - Organized by topic
  - Search-friendly format

### Configuration

- **[.marimushka.toml.example](.marimushka.toml.example)** - Configuration file example
- **[templates/README.md](templates/README.md)** - Template customization guide

### Security & Contributing

- **[SECURITY.md](SECURITY.md)** - Security features, best practices, and reporting
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute to the project
- **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)** - Community guidelines

### Quick Links

| I want to... | See... |
|-------------|--------|
| Get started quickly | [README.md - Installation](#-installation) |
| Fix an error | [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |
| See real examples | [RECIPES.md](docs/RECIPES.md) |
| Find a quick answer | [FAQ.md](docs/FAQ.md) |
| Upgrade versions | [MIGRATION.md](docs/MIGRATION.md) |
| Use the Python API | [API.md](API.md) |
| Deploy to GitHub Pages | [README.md - GitHub Action](#github-action) |
| Customize templates | [templates/README.md](templates/README.md) |
| Report a security issue | [SECURITY.md](SECURITY.md#reporting-a-vulnerability) |
| Contribute | [CONTRIBUTING.md](CONTRIBUTING.md) |

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 🙏 Acknowledgements

- [marimo](https://marimo.io) - The reactive Python notebook that powers this project
- [Jinja2](https://jinja.palletsprojects.com/) - The templating engine
used for HTML generation
- [uv](https://github.com/astral-sh/uv) - The fast Python package installer and resolver
