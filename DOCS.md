# Documentation Development Guide

This guide explains how to work with pydeflate's documentation.

## Overview

pydeflate uses [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) to generate documentation. The documentation is automatically built and deployed to GitHub Pages when changes are pushed to the `main` or `mkdocs` branch.

## Documentation Structure

```
docs/
├── index.md                    # Homepage
├── getting-started.md          # Setup and basic usage
├── deflate.md                 # Deflation examples
├── exchange.md                # Currency exchange examples
├── data-sources.md            # IMF, World Bank, OECD comparison
├── migration.md               # v1 to v2 migration guide
├── faq.md                     # FAQ and troubleshooting
└── advanced/
    ├── exceptions.md          # Error handling
    ├── context.md             # Context management
    ├── plugins.md             # Plugin system
    └── validation.md          # Schema validation
```

## Local Development

### Install Dependencies

```bash
# Install documentation dependencies
uv sync --group docs
```

### Build Documentation

```bash
# Build static site (output to site/)
uv run mkdocs build

# Build with strict mode (fail on warnings)
uv run mkdocs build --strict
```

### Live Preview

```bash
# Start development server with live reload
uv run mkdocs serve

# Open http://127.0.0.1:8000 in your browser
# Changes to markdown files will auto-reload
```

### Clean Build

```bash
# Remove previous build artifacts
uv run mkdocs build --clean
```

## Making Changes

### Editing Pages

1. Edit markdown files in `docs/` directory
2. Run `uv run mkdocs serve` to preview changes
3. Verify changes look correct in browser
4. Commit and push changes

### Adding New Pages

1. Create new `.md` file in appropriate `docs/` subdirectory
2. Add entry to `nav` section in `mkdocs.yml`:

```yaml
nav:
  - Home: index.md
  - Your New Page: your-page.md  # Add here
```

3. Preview with `mkdocs serve`
4. Commit changes

### Adding Admonitions

Use admonitions for tips, warnings, notes:

```markdown
!!! note
    This is a note

!!! tip
    This is a tip

!!! warning
    This is a warning

!!! danger
    This is a danger notice
```

### Code Blocks

Use syntax highlighting:

````markdown
```python
from pydeflate import imf_gdp_deflate

result = imf_gdp_deflate(df, base_year=2015)
```
````

### Tables

```markdown
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
```

### Internal Links

```markdown
[Link to another page](deflate.md)
[Link to section](deflate.md#gdp-deflator)
```

## Deployment

### Automatic Deployment

Documentation is automatically deployed to GitHub Pages when:

- Commits are pushed to `main` branch
- Commits are pushed to `mkdocs` branch
- Pull requests are created (build-only, no deploy)

The GitHub Actions workflow (`.github/workflows/docs.yml`) handles:

1. Installing dependencies
2. Building documentation
3. Deploying to `gh-pages` branch

### Manual Deployment

```bash
# Deploy to GitHub Pages manually
uv run mkdocs gh-deploy

# Deploy with custom commit message
uv run mkdocs gh-deploy -m "Updated documentation"
```

## Configuration

### mkdocs.yml

Main configuration file:

- **site_name**: Site title
- **nav**: Navigation structure
- **theme**: Material theme configuration
- **plugins**: Enabled plugins (search, minify, mkdocstrings)
- **markdown_extensions**: Markdown enhancements

### Theme Customization

Edit `mkdocs.yml` to customize:

```yaml
theme:
  name: material
  palette:
    primary: indigo  # Primary color
    accent: indigo   # Accent color
  features:
    - navigation.tabs  # Top-level tabs
    - search.suggest   # Search suggestions
```

## Best Practices

### Writing Style

- **Be concise**: Short paragraphs, clear sentences
- **Use examples**: Show, don't just tell
- **Be consistent**: Follow existing page structure
- **Test code**: Ensure code examples actually work

### Code Examples

- **Complete**: Include all necessary imports
- **Runnable**: Code should work if copy-pasted
- **Commented**: Explain non-obvious parts
- **Realistic**: Use realistic data and scenarios

### Organization

- **Progressive disclosure**: Start simple, add complexity gradually
- **Cross-reference**: Link to related pages
- **Group related content**: Keep related topics together

### Accessibility

- **Alt text**: Describe images (if any added)
- **Clear headings**: Use heading hierarchy properly
- **Descriptive links**: Avoid "click here", use descriptive text

## Troubleshooting

### Build Fails

```bash
# Check for syntax errors
uv run mkdocs build --strict

# Look for:
# - Broken internal links
# - Invalid YAML in front matter
# - Malformed tables or code blocks
```

### Pages Not Showing

- Check page is listed in `nav` section of `mkdocs.yml`
- Verify file path is correct (relative to `docs/`)
- Check file extension is `.md`

### Live Reload Not Working

- Restart `mkdocs serve`
- Check console for errors
- Verify file is saved

### GitHub Pages Not Updating

- Check GitHub Actions workflow status
- Verify `gh-pages` branch exists
- Check repository Settings → Pages configuration

## Documentation Standards

### File Naming

- Use lowercase with hyphens: `getting-started.md`
- Be descriptive: `error-handling.md` not `errors.md`
- Group related files in subdirectories

### Heading Levels

```markdown
# Page Title (H1 - only one per page)

## Section (H2)

### Subsection (H3)

#### Details (H4 - use sparingly)
```

### Code Style

- Use `python` for Python code blocks
- Use `bash` for shell commands
- Use `yaml` for YAML examples
- Indent with 4 spaces (matching project style)

## Resources

- [Material for MkDocs Documentation](https://squidfunk.github.io/mkdocs-material/)
- [MkDocs User Guide](https://www.mkdocs.org/user-guide/)
- [Python-Markdown Extensions](https://python-markdown.github.io/extensions/)
- [PyMdown Extensions](https://facelessuser.github.io/pymdown-extensions/)

## Contributing

To contribute to documentation:

1. Fork the repository
2. Create a branch: `git checkout -b docs/your-feature`
3. Make changes and test locally
4. Submit a pull request

The documentation will be built automatically on your PR to verify there are no errors.
