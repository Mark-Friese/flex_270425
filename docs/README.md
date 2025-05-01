# Flexibility Analysis System Documentation

This directory contains the documentation for the Flexibility Analysis System, built using [MkDocs](https://www.mkdocs.org/) with the [Material theme](https://squidfunk.github.io/mkdocs-material/).

## Building the Documentation

To build the documentation:

1. **Install MkDocs and the Material theme**:
   ```bash
   pip install mkdocs mkdocs-material
   ```

2. **Build the documentation**:
   ```bash
   cd firm_capacity_analysis  # Navigate to the directory containing mkdocs.yml
   mkdocs build               # Build static site to the 'site' directory
   ```

3. **Serve the documentation locally**:
   ```bash
   mkdocs serve               # Start a local server at http://127.0.0.1:8000/
   ```

## Documentation Structure

The documentation is organized into the following sections:

- **Installation**: Installation guides for different components
- **Usage**: User guides for different aspects of the system
- **Technical**: Technical documentation of mathematical models and algorithms
- **Development**: Guide for developers contributing to the project
- **Reference**: API reference, configuration options, and glossary

## Adding Pages

To add a new page to the documentation:

1. Create a new Markdown file in the appropriate directory
2. Add the page to the navigation in `mkdocs.yml`

Example:
```yaml
nav:
  - User Guide:
    - Getting Started: usage/index.md
    - New Page: usage/new-page.md  # Add this line
```

## Style Guide

When writing documentation:

- Use clear, concise language
- Include code examples where appropriate
- Use headings to organize content
- Include diagrams or images to illustrate complex concepts
- Document all parameters and return values for API functions
- Include examples for command-line options

## Math Equations

MathJax is configured to render LaTeX equations:

- Inline equations: `$E = mc^2$`
- Block equations:
  ```
  $$
  E(C) = \sum_{t} \max(D_t - C, 0) \cdot \Delta t
  $$
  ```

## Deploying the Documentation

The documentation is automatically built and deployed when changes are pushed to the main branch through GitHub Actions. The built documentation is available at [https://yourusername.github.io/flex_270425/](https://yourusername.github.io/flex_270425/).

## Contributing

Contributions to the documentation are welcome! Please follow the [development guide](development/index.md) when making changes.