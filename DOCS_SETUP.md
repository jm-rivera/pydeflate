# Documentation Setup Summary

This document provides a summary of the documentation setup for pydeflate using Material for MkDocs.

## What Was Created

### Documentation Files

Created comprehensive documentation in `docs/` directory:

- **index.md** - Homepage with overview, installation, quick start, key features
- **getting-started.md** - Detailed setup, DataFrame requirements, basic workflow
- **deflation.md** - All deflation functions with examples (IMF, World Bank, OECD DAC)
- **exchange.md** - Currency conversion examples and comparisons
- **data-sources.md** - Detailed comparison of IMF, World Bank, and OECD DAC sources
- **migration.md** - Complete v1 to v2 migration guide
- **faq.md** - Frequently asked questions and troubleshooting

#### Advanced Topics

- **advanced/exceptions.md** - Error handling patterns and best practices
- **advanced/context.md** - Context management for parallel ops and custom configs
- **advanced/plugins.md** - Creating custom data sources with plugin system
- **advanced/validation.md** - Schema validation setup and usage

### Configuration Files

- **mkdocs.yml** - Material for MkDocs configuration with theme, navigation, plugins
- **pyproject.toml** - Added `docs` dependency group with mkdocs-material, mkdocstrings
- **.github/workflows/docs.yml** - GitHub Actions workflow for automatic deployment

### Development Guides

- **DOCS.md** - Documentation development guide for contributors

## Quick Start

### View Documentation Locally

```bash
# Install dependencies
uv sync --group docs

# Start live preview server
uv run mkdocs serve

# Open http://127.0.0.1:8000
```

### Build Documentation

```bash
# Build static site
uv run mkdocs build

# Build with strict error checking
uv run mkdocs build --strict
```

### Deploy to GitHub Pages

Documentation automatically deploys when you push to `main` or `mkdocs` branch.

Manual deployment:

```bash
uv run mkdocs gh-deploy
```

## GitHub Pages Setup

After pushing the workflow, configure GitHub Pages:

1. Go to repository **Settings** → **Pages**
2. Under **Source**, select:
   - **Deploy from a branch**
   - Branch: `gh-pages`
   - Folder: `/ (root)`
3. Click **Save**

The documentation will be available at: `https://jm-rivera.github.io/pydeflate/`

## Documentation Features

### Material for MkDocs Theme

- Modern, responsive design
- Dark/light mode toggle
- Instant page loading
- Search functionality
- Code syntax highlighting with copy button
- Mobile-friendly navigation

### Navigation Structure

```
Home
├── Getting Started
User Guide
├── Deflation
├── Currency Exchange
└── Data Sources
Advanced
├── Error Handling
├── Context Management
├── Plugin System
└── Schema Validation
Migration Guide
FAQ
```

### Markdown Extensions

Enabled features:

- **Admonitions** - Tip, warning, note boxes
- **Code highlighting** - Syntax highlighting for Python, bash, YAML
- **Tables** - Markdown tables with styling
- **Tabs** - Tabbed content blocks
- **Emoji** - GitHub-style emoji support

### Plugins

- **search** - Full-text search
- **minify** - Minified HTML/CSS/JS for faster loading
- **mkdocstrings** - Auto-generate API docs from docstrings (available for future use)

## Content Highlights

### Example-Driven Approach

Every page includes practical, copy-paste ready examples:

```python
from pydeflate import imf_gdp_deflate, set_pydeflate_path

set_pydeflate_path("./data")

result = imf_gdp_deflate(
    data=df,
    base_year=2015,
    source_currency="USA",
    target_currency="EUR",
    ...
)
```

### Comprehensive Coverage

- All 7 deflation functions documented with examples
- All 4 exchange functions documented
- 3 data sources compared in detail
- Advanced features (plugins, contexts, validation) fully explained
- Migration guide from v1 to v2
- FAQ with troubleshooting

### Best Practices

Documentation includes:

- When to use each deflator type
- Error handling patterns
- Performance optimization tips
- Testing strategies
- Production deployment examples

## Maintenance

### Updating Documentation

1. Edit markdown files in `docs/`
2. Test locally: `uv run mkdocs serve`
3. Commit and push to `main` or `mkdocs` branch
4. GitHub Actions automatically builds and deploys

### Adding New Pages

1. Create `.md` file in `docs/`
2. Add to `nav` section in `mkdocs.yml`
3. Cross-reference from related pages
4. Test build: `uv run mkdocs build --strict`

### Versioning (Future)

To add versioned docs with mike:

```bash
# Install mike
uv pip install mike

# Deploy version
uv run mike deploy 2.2 latest --push

# Set default version
uv run mike set-default latest --push
```

## Troubleshooting

### Documentation Not Deploying

1. Check GitHub Actions workflow status in **Actions** tab
2. Verify `gh-pages` branch was created
3. Check GitHub Pages settings (Settings → Pages)
4. Ensure workflow has write permissions (Settings → Actions → General)

### Build Errors

```bash
# Check for errors with strict mode
uv run mkdocs build --strict

# Common issues:
# - Broken internal links
# - Missing files referenced in nav
# - Invalid markdown syntax
```

### Links Not Working

- Use relative paths: `[Link](other-page.md)`
- For sections: `[Link](other-page.md#section-name)`
- For external: `[Link](https://example.com)`

## Next Steps

1. **Push to GitHub** - The workflow will trigger on push
2. **Configure GitHub Pages** - Set source to `gh-pages` branch
3. **Review deployed docs** - Check https://jm-rivera.github.io/pydeflate/
4. **Add documentation badge to README** (optional):

```markdown
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://jm-rivera.github.io/pydeflate/)
```

## Resources

- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [MkDocs User Guide](https://www.mkdocs.org/)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [DOCS.md](DOCS.md) - Detailed development guide

## Support

For documentation issues:

- Check [DOCS.md](DOCS.md) for development guide
- Review Material for MkDocs documentation
- Open issue on GitHub for bugs or suggestions
