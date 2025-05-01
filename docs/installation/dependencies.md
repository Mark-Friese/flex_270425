# Dependencies

This page outlines the dependencies required to install and run the Flexibility Analysis System.

## Python Requirements

The Flexibility Analysis System requires Python 3.8 or newer. The system has been tested with the following Python versions:

- Python 3.8
- Python 3.9
- Python 3.10
- Python 3.11

## Core Dependencies

The core dependencies for the Flexibility Analysis System are listed in the `requirements.txt` file:

```bash
# Core data processing
pandas>=2.0.0
numpy>=2.0.0
matplotlib>=3.10.0

# Configuration and file handling
PyYAML>=6.0.0
pyarrow>=20.0.0  # For parquet file support

# Utilities
psutil>=7.0.0    # For system monitoring
platformdirs>=4.3.0
```

## Optional Dependencies

### Parquet Processing

For processing parquet files, additional dependencies are required:

```bash
# Parquet processing
pyarrow>=20.0.0
pandas>=2.0.0
dask>=2025.4.1      # For larger-than-memory processing
distributed>=2025.4.1
```

### Desktop Application

For the desktop application, the following additional dependencies are required:

```bash
# Desktop application
pywebview>=4.2.2    # Web-based UI framework
Pillow>=9.0.0       # Image processing
PyInstaller>=5.6.0  # For building standalone executables
```

### Testing

For running tests:

```bash
pytest>=8.0.0
```

## Installing Dependencies

### Using pip

You can install all required dependencies using pip:

```bash
# Install core dependencies
pip install -r requirements.txt

# Install desktop application dependencies
pip install -r packaging_requirements.txt

# Install testing dependencies
pip install -r requirements-test.txt
```

### Using the Install Script

For convenience, you can use the provided installation script that handles platform-specific dependencies:

```bash
python install_dependencies.py
```

This script will:

1. Install the appropriate dependencies for your platform
2. Skip platform-specific packages on incompatible systems
3. Ensure all version requirements are met

## Platform-Specific Notes

### Windows

On Windows, additional dependencies might be required:

```bash
pywin32>=310  # Required for desktop application on Windows
```

This is automatically handled by the `install_dependencies.py` script.

### Linux

On Linux, ensure you have the appropriate system packages installed for PyWebView:

```bash
# For Debian/Ubuntu
sudo apt-get install python3-dev python3-setuptools python3-tk python3-wheel
sudo apt-get install libgtk-3-dev libwebkit2gtk-4.0-dev

# For Fedora/RHEL
sudo dnf install python3-devel gtk3-devel webkit2gtk3-devel
```

### macOS

On macOS, ensure you have Python installed via Homebrew or the official installer:

```bash
# Using Homebrew
brew install python
```

## Virtual Environments

It's recommended to use a virtual environment to avoid conflicts with other Python packages:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

# Install dependencies in the virtual environment
pip install -r requirements.txt
```

## Dependency Conflicts

If you encounter dependency conflicts, you can use the platform-independent requirements file:

```bash
pip install -r requirements-cross-platform.txt
```

This file excludes platform-specific packages that might cause installation issues on certain systems.