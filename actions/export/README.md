# Marimushka Export Action

This GitHub Action exports [marimo](https://marimo.io) notebooks and apps
to static HTML and WebAssembly for deployment to GitHub Pages or other static hosting.

## Features

- Export marimo notebooks to static HTML
- Export marimo notebooks to interactive WebAssembly (edit mode)
- Export marimo apps to WebAssembly applications (run mode with hidden code)
- Customizable templates for the index page
- Automatic artifact upload

## Usage

Add the following to your GitHub workflow file:

```yaml
jobs:
  export:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Export marimo notebooks
        uses: jebel-quant/marimushka/actions/export@v1
        with:
          notebooks: 'notebooks'  # Directory containing notebook files
          apps: 'apps'            # Directory containing app files
          # Optional parameters:
          # template: 'path/to/custom/template.html.j2'
          # notebooks_wasm: 'notebooks'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `notebooks` | Directory containing marimo notebook files (.py) to be exported as static HTML notebooks. | No | `notebooks` |
| `apps` | Directory containing marimo app files (.py) to be exported as WebAssembly applications with hidden code (run mode). | No | `apps` |
| `notebooks_wasm` | Directory containing marimo notebook files (.py) to be exported as interactive WebAssembly notebooks with editable code (edit mode). | No | `notebooks` |
| `template` | Path to a custom Jinja2 template file (.html.j2) for the index page. If not provided, the default Tailwind CSS template will be used. | No | |

## Outputs

The action uploads the exported files as an artifact named `marimushka`.
You can download this artifact in subsequent steps or jobs.

## Example: Export and Deploy to GitHub Pages

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
        uses: jebel-quant/marimushka/actions/export@v1
        with:
          notebooks: 'notebooks'
          apps: 'apps'

      - name: Deploy to GitHub Pages
        uses: JamesIves/github-pages-deploy-action@v4
        with:
          folder: artifacts/marimushka
          branch: gh-pages
```

## Example: Custom Template

```yaml
- name: Export with custom template
  uses: jebel-quant/marimushka/actions/export@v1
  with:
    notebooks: 'notebooks'
    template: 'templates/my-custom-template.html.j2'
```

## License

This project is licensed under the Apache License 2.0 - see the
LICENSE file for details.
