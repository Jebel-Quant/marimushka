# Recipes

This guide provides real-world recipes and patterns for using Marimushka effectively.

## Table of Contents

- [Basic Workflows](#basic-workflows)
- [CI/CD Integration](#cicd-integration)
- [Custom Templates](#custom-templates)
- [Advanced Patterns](#advanced-patterns)
- [Deployment Strategies](#deployment-strategies)
- [Development Workflows](#development-workflows)

---

## Basic Workflows

### Recipe 1: Simple Documentation Site

**Scenario**: Convert a folder of notebooks into a static documentation site.

```bash
# Project structure
project/
├── notebooks/
│   ├── intro.py
│   ├── tutorial.py
│   └── advanced.py
└── .marimushka.toml

# .marimushka.toml
[marimushka]
output = "_site"
notebooks = "notebooks"
sandbox = true

# Export
uvx marimushka export

# Serve locally
cd _site
python -m http.server 8000
# Visit: http://localhost:8000
```

---

### Recipe 2: Mixed Notebook Types

**Scenario**: Static notebooks for docs, interactive for tutorials, apps for tools.

```bash
# Project structure
project/
├── docs/              # Static documentation
│   ├── intro.py
│   └── guide.py
├── tutorials/         # Interactive tutorials
│   ├── basics.py
│   └── advanced.py
└── tools/            # Standalone apps
    ├── calculator.py
    └── visualizer.py

# Export with different types
uvx marimushka export \
  --notebooks docs \
  --notebooks-wasm tutorials \
  --apps tools \
  --output _site
```

**Result**:
- Docs: Fast-loading, static HTML
- Tutorials: Editable, interactive in browser
- Tools: Clean UI with hidden code

---

### Recipe 3: Quick Preview During Development

**Scenario**: Test notebook appearance while developing.

```bash
# Option 1: Single export
uvx marimushka export && open _site/index.html

# Option 2: Watch mode (auto-reload)
uvx marimushka watch &
python -m http.server --directory _site 8000

# Edit notebooks, refresh browser to see changes
```

---

## CI/CD Integration

### Recipe 4: GitHub Pages with GitHub Actions

**Scenario**: Automatically publish notebooks to GitHub Pages on every push.

**.github/workflows/publish.yml**:
```yaml
name: Publish Notebooks

on:
  push:
    branches: [main]

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  export:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Export notebooks
        uses: jebel-quant/marimushka@v0.2.3
        with:
          notebooks: 'docs/notebooks'
          apps: 'docs/apps'
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v2
        with:
          path: artifacts/marimushka
  
  deploy:
    needs: export
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v2
```

**Setup**:
1. Enable Pages: Settings → Pages → Source: GitHub Actions
2. Push to main branch
3. Visit: `https://username.github.io/repo-name/`

---

### Recipe 5: Deploy to Netlify

**Scenario**: Deploy to Netlify for faster builds and custom domains.

**.github/workflows/netlify.yml**:
```yaml
name: Deploy to Netlify

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Export notebooks
        uses: jebel-quant/marimushka@v0.2.3
      
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

**Setup**:
1. Create Netlify site
2. Add secrets to repository: `NETLIFY_AUTH_TOKEN`, `NETLIFY_SITE_ID`
3. Push to main

---

### Recipe 6: Deploy to AWS S3 + CloudFront

**Scenario**: Deploy to S3 with CloudFront CDN for global distribution.

**.github/workflows/aws.yml**:
```yaml
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
        uses: jebel-quant/marimushka@v0.2.3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Upload to S3
        run: |
          aws s3 sync artifacts/marimushka/ s3://my-bucket/notebooks/ \
            --delete \
            --cache-control "public, max-age=3600"
      
      - name: Invalidate CloudFront
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CLOUDFRONT_DIST_ID }} \
            --paths "/*"
```

---

### Recipe 7: GitLab CI/CD

**Scenario**: Use GitLab CI for automated deployment.

**.gitlab-ci.yml**:
```yaml
stages:
  - export
  - deploy

export:
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
    - export
  script:
    - echo "Deploying to GitLab Pages"
  artifacts:
    paths:
      - public
  only:
    - main
```

**Result**: Notebooks available at `https://username.gitlab.io/project`

---

## Custom Templates

### Recipe 8: Corporate Branding Template

**Scenario**: Create a branded template matching your company's design.

**templates/corporate.html.j2**:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Company Notebooks</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --brand-primary: #0066cc;
            --brand-secondary: #f0f4f8;
            --brand-text: #1a1a1a;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: var(--brand-secondary);
            color: var(--brand-text);
        }
        .header {
            background: white;
            padding: 2rem;
            border-bottom: 3px solid var(--brand-primary);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .logo {
            font-size: 2rem;
            font-weight: 700;
            color: var(--brand-primary);
        }
        .container { max-width: 1200px; margin: 2rem auto; padding: 0 2rem; }
        .section { background: white; padding: 2rem; margin-bottom: 2rem; border-radius: 8px; }
        .section h2 {
            color: var(--brand-primary);
            border-bottom: 2px solid var(--brand-secondary);
            padding-bottom: 0.5rem;
            margin-bottom: 1rem;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-top: 1.5rem;
        }
        .card {
            padding: 1.5rem;
            background: var(--brand-secondary);
            border-radius: 8px;
            text-decoration: none;
            color: inherit;
            transition: transform 0.2s, box-shadow 0.2s;
            display: block;
        }
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,102,204,0.15);
        }
        .card h3 {
            color: var(--brand-primary);
            margin-bottom: 0.5rem;
        }
        .footer {
            text-align: center;
            padding: 2rem;
            color: #666;
            font-size: 0.875rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <div class="logo">🏢 Company Data Science</div>
            <p style="margin-top: 0.5rem; color: #666;">Interactive Notebooks & Analytics</p>
        </div>
    </div>
    
    <div class="container">
        {% if notebooks %}
        <div class="section">
            <h2>📊 Documentation</h2>
            <div class="grid">
                {% for nb in notebooks %}
                <a href="{{ nb.html_path }}" class="card">
                    <h3>{{ nb.display_name }}</h3>
                    <p style="color: #666; font-size: 0.875rem; margin-top: 0.5rem;">
                        Static notebook
                    </p>
                </a>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        {% if notebooks_wasm %}
        <div class="section">
            <h2>🎓 Interactive Tutorials</h2>
            <div class="grid">
                {% for nb in notebooks_wasm %}
                <a href="{{ nb.html_path }}" class="card">
                    <h3>{{ nb.display_name }}</h3>
                    <p style="color: #666; font-size: 0.875rem; margin-top: 0.5rem;">
                        ⚡ Interactive • Editable
                    </p>
                </a>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        {% if apps %}
        <div class="section">
            <h2>🛠️ Analytics Tools</h2>
            <div class="grid">
                {% for app in apps %}
                <a href="{{ app.html_path }}" class="card">
                    <h3>{{ app.display_name }}</h3>
                    <p style="color: #666; font-size: 0.875rem; margin-top: 0.5rem;">
                        🚀 Ready to use
                    </p>
                </a>
                {% endfor %}
            </div>
        </div>
        {% endif %}
    </div>
    
    <div class="footer">
        © 2025 Your Company. Generated with Marimushka.
    </div>
</body>
</html>
```

**Usage**:
```bash
uvx marimushka export --template templates/corporate.html.j2
```

---

### Recipe 9: Dark Theme Template

**Scenario**: Create a dark mode template for better readability.

**templates/dark.html.j2**:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notebooks - Dark Mode</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 2rem;
            line-height: 1.6;
        }
        h1 {
            color: #58a6ff;
            margin-bottom: 2rem;
            font-size: 2.5rem;
        }
        h2 {
            color: #79c0ff;
            margin: 2rem 0 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #30363d;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-top: 1.5rem;
        }
        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 1.5rem;
            text-decoration: none;
            color: inherit;
            display: block;
            transition: all 0.2s;
        }
        .card:hover {
            background: #1c2128;
            border-color: #58a6ff;
            transform: translateY(-2px);
        }
        .card h3 {
            color: #58a6ff;
            margin-bottom: 0.5rem;
        }
        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-top: 0.5rem;
        }
        .badge-static { background: #1f6feb; color: white; }
        .badge-interactive { background: #238636; color: white; }
        .badge-app { background: #9e6a03; color: white; }
    </style>
</head>
<body>
    <h1>🌙 Notebooks</h1>
    
    {% if notebooks %}
    <section>
        <h2>Static Notebooks</h2>
        <div class="grid">
            {% for nb in notebooks %}
            <a href="{{ nb.html_path }}" class="card">
                <h3>{{ nb.display_name }}</h3>
                <span class="badge badge-static">Static</span>
            </a>
            {% endfor %}
        </div>
    </section>
    {% endif %}
    
    {% if notebooks_wasm %}
    <section>
        <h2>Interactive Notebooks</h2>
        <div class="grid">
            {% for nb in notebooks_wasm %}
            <a href="{{ nb.html_path }}" class="card">
                <h3>{{ nb.display_name }}</h3>
                <span class="badge badge-interactive">Interactive</span>
            </a>
            {% endfor %}
        </div>
    </section>
    {% endif %}
    
    {% if apps %}
    <section>
        <h2>Applications</h2>
        <div class="grid">
            {% for app in apps %}
            <a href="{{ app.html_path }}" class="card">
                <h3>{{ app.display_name }}</h3>
                <span class="badge badge-app">App</span>
            </a>
            {% endfor %}
        </div>
    </section>
    {% endif %}
</body>
</html>
```

---

## Advanced Patterns

### Recipe 10: Filtered Export

**Scenario**: Export only notebooks matching a pattern (e.g., exclude drafts).

**export_filtered.py**:
```python
#!/usr/bin/env python3
"""Export notebooks, excluding drafts."""

from pathlib import Path
from marimushka.notebook import folder2notebooks, Kind
from marimushka.export import _generate_index

def export_filtered(exclude_prefix="_draft"):
    output = Path("_site")
    output.mkdir(parents=True, exist_ok=True)
    
    # Get all notebooks
    all_notebooks = folder2notebooks("notebooks", Kind.NB)
    all_apps = folder2notebooks("apps", Kind.APP)
    
    # Filter out drafts
    notebooks = [nb for nb in all_notebooks 
                 if not nb.path.stem.startswith(exclude_prefix)]
    apps = [app for app in all_apps 
            if not app.path.stem.startswith(exclude_prefix)]
    
    print(f"Found {len(all_notebooks)} notebooks, exporting {len(notebooks)}")
    print(f"Found {len(all_apps)} apps, exporting {len(apps)}")
    
    # Export
    template = Path(__file__).parent / "templates" / "tailwind.html.j2"
    _generate_index(
        output=output,
        template_file=template,
        notebooks=notebooks,
        apps=apps,
        notebooks_wasm=[],
        sandbox=True
    )

if __name__ == "__main__":
    export_filtered()
```

**Usage**:
```bash
# Notebooks starting with _draft will be excluded
touch notebooks/_draft_analysis.py
python export_filtered.py
```

---

### Recipe 11: Pre-export Data Generation

**Scenario**: Generate data files before exporting notebooks.

**build.sh**:
```bash
#!/bin/bash
set -e

echo "🔨 Generating data..."
python scripts/generate_data.py

echo "📊 Exporting notebooks..."
uvx marimushka export

echo "✅ Build complete!"
```

**scripts/generate_data.py**:
```python
import pandas as pd
from pathlib import Path

# Generate sample data
data = {
    'date': pd.date_range('2024-01-01', periods=100),
    'value': range(100)
}
df = pd.DataFrame(data)

# Save for notebooks to use
output_dir = Path('data')
output_dir.mkdir(exist_ok=True)
df.to_csv(output_dir / 'sample.csv', index=False)

print("✓ Data generated")
```

---

### Recipe 12: Multi-Project Export

**Scenario**: Export notebooks from multiple projects to a single site.

**export_multi.py**:
```python
#!/usr/bin/env python3
"""Export notebooks from multiple projects."""

from pathlib import Path
from marimushka.export import main
import shutil

projects = [
    {
        'name': 'data-science',
        'notebooks': 'projects/data-science/notebooks',
        'apps': 'projects/data-science/apps'
    },
    {
        'name': 'machine-learning',
        'notebooks': 'projects/ml/notebooks',
        'apps': 'projects/ml/apps'
    }
]

output_base = Path('_site')
output_base.mkdir(exist_ok=True)

for project in projects:
    print(f"📦 Exporting {project['name']}...")
    
    project_output = output_base / project['name']
    
    main(
        notebooks=project['notebooks'],
        apps=project['apps'],
        output=str(project_output)
    )

# Create top-level index
index_html = """<!DOCTYPE html>
<html>
<head><title>Projects</title></head>
<body>
    <h1>Projects</h1>
    <ul>
        <li><a href="data-science/">Data Science</a></li>
        <li><a href="machine-learning/">Machine Learning</a></li>
    </ul>
</body>
</html>"""

(output_base / 'index.html').write_text(index_html)
print("✅ Multi-project export complete!")
```

---

## Deployment Strategies

### Recipe 13: Blue-Green Deployment

**Scenario**: Deploy new version without downtime.

```bash
#!/bin/bash
# blue-green-deploy.sh

# Export to staging
uvx marimushka export --output _site_green

# Test staging
python -m http.server --directory _site_green 8001 &
TEST_PID=$!
sleep 2

# Run smoke tests
curl http://localhost:8001/ > /dev/null || exit 1
curl http://localhost:8001/notebooks/intro.html > /dev/null || exit 1

kill $TEST_PID

# Swap blue/green
mv _site _site_blue_old
mv _site_green _site

# Restart server
systemctl restart notebook-server

echo "✅ Deployed successfully"
```

---

### Recipe 14: Versioned Documentation

**Scenario**: Keep multiple versions of documentation.

```bash
# Structure
docs/
├── latest/
├── v0.2/
└── v0.1/

# Export with version
VERSION=v0.3
uvx marimushka export --output docs/$VERSION

# Update latest
rm -rf docs/latest
cp -r docs/$VERSION docs/latest

# Generate version selector
cat > docs/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head><title>Documentation</title></head>
<body>
    <h1>Documentation</h1>
    <ul>
        <li><a href="latest/">Latest</a></li>
        <li><a href="v0.3/">v0.3</a></li>
        <li><a href="v0.2/">v0.2</a></li>
    </ul>
</body>
</html>
EOF
```

---

## Development Workflows

### Recipe 15: Local Development Server

**Scenario**: Live reload during development.

**dev-server.sh**:
```bash
#!/bin/bash

# Start HTTP server
python -m http.server --directory _site 8000 &
SERVER_PID=$!

# Start watch mode
uvx marimushka watch

# Cleanup on exit
trap "kill $SERVER_PID" EXIT
```

**Usage**:
```bash
chmod +x dev-server.sh
./dev-server.sh

# Visit: http://localhost:8000
# Edit notebooks, page auto-updates
```

---

### Recipe 16: Pre-commit Hook

**Scenario**: Auto-export notebooks before committing.

**.git/hooks/pre-commit**:
```bash
#!/bin/bash

echo "🔄 Exporting notebooks..."
uvx marimushka export --output _site

# Add exported files to commit
git add _site/

echo "✅ Export complete"
```

**Setup**:
```bash
chmod +x .git/hooks/pre-commit
```

---

### Recipe 17: Notebook Testing Pipeline

**Scenario**: Test notebooks before deploying.

**.github/workflows/test.yml**:
```yaml
name: Test Notebooks

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Test notebooks execute
        run: |
          pip install uv
          for nb in notebooks/*.py; do
            echo "Testing $nb..."
            uvx marimo run "$nb" --sandbox --headless
          done
      
      - name: Test export
        uses: jebel-quant/marimushka@v0.2.3
      
      - name: Verify output
        run: |
          test -f artifacts/marimushka/index.html
          test -d artifacts/marimushka/notebooks/
```

---

## Tips and Best Practices

### Performance

```bash
# Use parallel export for speed
uvx marimushka export --parallel --max-workers 8

# Sequential for debugging
uvx marimushka export --no-parallel
```

### Security

```bash
# Always use sandbox in production
uvx marimushka export --sandbox

# Enable audit logging
# .marimushka.toml
[marimushka.security]
audit_enabled = true
```

### Organization

```bash
# Organize by purpose
project/
├── docs/          # Documentation (static)
├── tutorials/     # Learning (interactive)
└── tools/        # Applications (apps)
```

---

**Need more recipes?**

- Check [API.md](API.md) for programmatic patterns
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Visit [FAQ.md](FAQ.md) for quick answers
