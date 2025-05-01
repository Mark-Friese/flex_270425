# CI/CD Integration

This document explains how the Flexibility Analysis System is integrated with Continuous Integration and Continuous Deployment (CI/CD) pipelines to ensure code quality and automate testing, documentation, and deployment processes.

## Overview

The CI/CD pipeline automates the following processes:

1. **Testing**: Run automated tests on code changes
2. **Documentation**: Build and deploy documentation
3. **Packaging**: Create installable packages and executables
4. **Deployment**: Deploy to target environments

## GitHub Actions Workflows

The project uses GitHub Actions for CI/CD automation. The workflows are defined in the `.github/workflows/` directory.

### Testing Workflow

The main testing workflow is defined in `.github/workflows/test-flexibility-analysis.yml`:

```yaml
name: Test Flexibility Analysis

on:
  push:
    branches: [ main, develop ]
    paths:
      - "firm_capacity_analysis/**"
      - ".github/workflows/test-flexibility-analysis.yml"
  pull_request:
    branches: [ main, develop ]
    paths:
      - "firm_capacity_analysis/**"
      - ".github/workflows/test-flexibility-analysis.yml"

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r firm_capacity_analysis/requirements-test.txt
        
    - name: Run tests
      run: |
        cd firm_capacity_analysis
        python -m pytest tests/
        
    - name: Generate coverage report
      run: |
        cd firm_capacity_analysis
        python -m pytest --cov=src --cov=competition_builder --cov=service_windows --cov-report=xml tests/
        
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./firm_capacity_analysis/coverage.xml
        fail_ci_if_error: false
```

This workflow:
- Runs on all pushes to `main` and `develop` branches
- Runs on all pull requests to `main` and `develop` branches
- Sets up Python 3.11
- Installs test dependencies
- Runs all tests
- Generates a coverage report
- Uploads coverage data to Codecov (if configured)

### Documentation Workflow

The documentation workflow is defined in `.github/workflows/build-docs.yml`:

```yaml
name: Build Documentation

on:
  push:
    branches: [ main ]
    paths:
      - "firm_capacity_analysis/docs/**"
      - "firm_capacity_analysis/mkdocs.yml"
      - ".github/workflows/build-docs.yml"

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install mkdocs mkdocs-material
        
    - name: Build documentation
      run: |
        cd firm_capacity_analysis
        mkdocs build
        
    - name: Deploy to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./firm_capacity_analysis/site
```

This workflow:
- Runs on all pushes to the `main` branch that affect documentation
- Sets up Python 3.11
- Installs MkDocs and the Material theme
- Builds the documentation
- Deploys the built documentation to GitHub Pages

### Packaging Workflow

The packaging workflow is defined in `.github/workflows/build-package.yml`:

```yaml
name: Build Package

on:
  release:
    types: [published]

jobs:
  build_windows:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r firm_capacity_analysis/requirements.txt
        pip install -r firm_capacity_analysis/packaging_requirements.txt
        
    - name: Build Windows executable
      run: |
        cd firm_capacity_analysis
        python build.py
        
    - name: Upload Windows artifact
      uses: actions/upload-artifact@v3
      with:
        name: FlexibilityAnalysisSystem-Windows
        path: firm_capacity_analysis/dist/FlexibilityAnalysisSystem/
  
  build_macos:
    runs-on: macos-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r firm_capacity_analysis/requirements.txt
        pip install -r firm_capacity_analysis/packaging_requirements.txt
        
    - name: Build macOS package
      run: |
        cd firm_capacity_analysis
        python build.py
        
    - name: Upload macOS artifact
      uses: actions/upload-artifact@v3
      with:
        name: FlexibilityAnalysisSystem-macOS
        path: firm_capacity_analysis/dist/FlexibilityAnalysisSystem.app/
```

This workflow:
- Runs when a release is published
- Builds executables for Windows and macOS
- Uploads the built executables as artifacts

## Configuring CI/CD

### Setting Up GitHub Actions

To set up GitHub Actions for your fork or clone of the repository:

1. Ensure the `.github/workflows/` directory exists with the workflow files
2. Enable GitHub Actions in your repository settings
3. Configure any required secrets (e.g., for deployment)

### Configuring Codecov

To configure Codecov for coverage reporting:

1. Sign up at [codecov.io](https://codecov.io) with your GitHub account
2. Add your repository to Codecov
3. Add the Codecov token as a secret in your GitHub repository settings
4. Update the workflow file to use the token:

```yaml
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    token: ${{ secrets.CODECOV_TOKEN }}
    file: ./firm_capacity_analysis/coverage.xml
    fail_ci_if_error: false
```

### Configuring GitHub Pages

To configure GitHub Pages for documentation:

1. Go to your repository settings
2. In the "Pages" section, select the `gh-pages` branch as the source
3. Ensure the workflow has permission to push to this branch

## Local CI/CD Development

To test CI/CD workflows locally before pushing to GitHub:

### Local Testing

1. Install `act` to run GitHub Actions locally:
   ```bash
   # macOS
   brew install act
   
   # Linux
   curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
   ```

2. Run workflows locally:
   ```bash
   act -j test
   act -j build
   ```

### Local Documentation Building

To build and serve the documentation locally:

```bash
cd firm_capacity_analysis
mkdocs serve
```

This will start a local server at http://127.0.0.1:8000/ that updates automatically when documentation files change.

## Troubleshooting CI/CD Issues

### Common Workflow Issues

1. **Missing dependencies**: Ensure all dependencies are listed in the requirements files
2. **Permission issues**: Check that workflows have appropriate permissions
3. **Secrets not available**: Verify secret configuration in repository settings
4. **Path issues**: Ensure paths in workflow files match your repository structure

### Debugging Workflow Runs

To debug workflow runs:

1. Enable debug logging by setting a secret called `ACTIONS_STEP_DEBUG` to `true`
2. Add diagnostic steps to your workflow:

```yaml
- name: Debug information
  run: |
    pwd
    ls -la
    python --version
    pip list
```

## Best Practices

1. **Keep workflows focused**: Each workflow should have a clear, single purpose
2. **Cache dependencies**: Use caching to speed up workflow runs:

```yaml
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

3. **Test workflows before merging**: Verify workflow changes on a branch before merging
4. **Use matrix builds**: For testing across multiple Python versions or operating systems:

```yaml
strategy:
  matrix:
    python-version: [3.8, 3.9, 3.10, 3.11]
    os: [ubuntu-latest, windows-latest, macos-latest]
```

5. **Set up status badges**: Add status badges to your README.md to show CI/CD status:

```markdown
[![Tests](https://github.com/yourusername/flex_270425/actions/workflows/test-flexibility-analysis.yml/badge.svg)](https://github.com/yourusername/flex_270425/actions/workflows/test-flexibility-analysis.yml)
[![Documentation](https://github.com/yourusername/flex_270425/actions/workflows/build-docs.yml/badge.svg)](https://github.com/yourusername/flex_270425/actions/workflows/build-docs.yml)
```

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [MkDocs Documentation](https://www.mkdocs.org/)
- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [Codecov Documentation](https://docs.codecov.io/)