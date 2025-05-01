# Installation Guide

This guide covers the installation of the Flexibility Analysis System, including all dependencies and optional components.

## Prerequisites

Before installing the system, ensure you have:

- Python 3.8 or newer
- pip (Python package installer)
- Git (optional, for cloning the repository)

## Basic Installation

1. **Clone or download the repository**:
   ```bash
   git clone https://github.com/yourusername/flex_270425.git
   cd flex_270425
   ```

2. **Install required dependencies**:
   ```bash
   # Install from the requirements file
   pip install -r firm_capacity_analysis/requirements.txt
   ```

3. **Install platform-specific dependencies** (optional):
   ```bash
   # Run the installer script which handles platform-specific packages
   python firm_capacity_analysis/install_dependencies.py
   ```

## Development Installation

For development work:

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install development dependencies**:
   ```bash
   pip install -r firm_capacity_analysis/requirements-test.txt
   ```

3. **Install optional packages for testing**:
   ```bash
   pip install pytest pytest-cov matplotlib
   ```

## MkDocs Installation (for Documentation)

To build and serve the documentation:

1. **Install MkDocs and the Material theme**:
   ```bash
   pip install mkdocs mkdocs-material
   ```

2. **Build the documentation**:
   ```bash
   cd firm_capacity_analysis
   mkdocs build
   ```

3. **Serve the documentation locally**:
   ```bash
   mkdocs serve
   ```

## Desktop Application Installation

See [Desktop Application Installation](desktop-app.md) for instructions on installing and running the desktop application.

## Troubleshooting

If you encounter issues during installation:

1. **Dependency conflicts**: Try installing in a fresh virtual environment
2. **Platform-specific issues**: Check the [Dependencies](dependencies.md) page
3. **Permission errors**: Use `pip install --user` or run with administrator privileges

For more help, [submit an issue](https://github.com/yourusername/flex_270425/issues) on GitHub.