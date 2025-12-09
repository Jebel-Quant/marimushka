# 📦 marimushka

[![PyPI version](https://badge.fury.io/py/marimushka.svg)](https://badge.fury.io/py/marimushka)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/jebel-quant/marimushka/release.yml?label=release)](https://github.com/jebel-quant/marimushka/actions/workflows/release.yml)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Created with qCradle](https://img.shields.io/badge/Created%20with-qCradle-blue?style=flat-square)](https://github.com/tschm/package)
[![GitHub stars](https://img.shields.io/github/stars/jebel-quant/marimushka)](https://github.com/jebel-quant/marimushka/stargazers)

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
- 🧩 **Flexible configuration** with command-line options and Python API

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
        uses: jebel-quant/marimushka@v0.0.26
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
        uses: jebel-quant/marimushka@0.0.26
        with:
          notebooks: 'notebooks'
          apps: 'apps'

      - name: Deploy to GitHub Pages
        uses: JamesIves/github-pages-deploy-action@v4
        with:
          folder: artifacts/marimushka
          branch: gh-pages
```

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

### Running Tests

To run the tests, you'll need to install the development dependencies:

```bash
# Install the package with development dependencies
pip install -e ".[dev]"

# Or with uv (recommended)
uv pip install -e ".[dev]"
```

Then you can run the tests using pytest:

```bash
# Run tests with pytest
pytest src/tests/ -v

# Or use the make command
make test
```

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 🙏 Acknowledgements

- [marimo](https://marimo.io) - The reactive Python notebook that powers this project
- [Jinja2](https://jinja.palletsprojects.com/) - The templating engine
used for HTML generation
- [uv](https://github.com/astral-sh/uv) - The fast Python package installer and resolver
