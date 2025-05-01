# Contributing to the Flexibility Analysis System

This guide provides information for developers who want to contribute to the Flexibility Analysis System. Thank you for your interest in improving this project!

## Getting Started

### Prerequisites

Before you begin, make sure you have:

1. **Python 3.8+**: The project requires Python 3.8 or newer
2. **Git**: For version control
3. **Development environment**: Your favorite IDE or text editor (VS Code, PyCharm, etc.)

### Setting Up a Development Environment

1. **Fork the repository**:
   - Visit [https://github.com/yourusername/flex_270425](https://github.com/yourusername/flex_270425)
   - Click the "Fork" button in the top right corner

2. **Clone your fork**:
   ```bash
   git clone https://github.com/your-username/flex_270425.git
   cd flex_270425
   ```

3. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

4. **Install development dependencies**:
   ```bash
   pip install -r firm_capacity_analysis/requirements-test.txt
   ```

5. **Set up pre-commit hooks** (optional):
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Development Workflow

### Branching Strategy

The project follows a Git Flow-inspired branching strategy:

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/xxx`: Feature branches
- `bugfix/xxx`: Bug fix branches
- `release/xxx`: Release preparation branches

### Making Changes

1. **Create a new branch**:
   ```bash
   # For a new feature
   git checkout -b feature/my-new-feature develop
   
   # For a bug fix
   git checkout -b bugfix/issue-number develop
   ```

2. **Make your changes**: Implement your feature or fix

3. **Write tests**: Add tests for your changes

4. **Run tests locally**:
   ```bash
   cd firm_capacity_analysis
   python -m pytest
   ```

5. **Check code style**:
   ```bash
   # If you have pre-commit hooks installed
   pre-commit run --all-files
   
   # Otherwise, manually run style checks
   flake8 firm_capacity_analysis
   mypy firm_capacity_analysis
   ```

6. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

7. **Update your branch with latest changes**:
   ```bash
   git checkout develop
   git pull
   git checkout feature/my-new-feature
   git rebase develop
   ```

8. **Push your branch**:
   ```bash
   git push -u origin feature/my-new-feature
   ```

9. **Create a pull request**:
   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Select your branch and the target branch (usually `develop`)
   - Fill out the pull request template

## Pull Request Process

1. **Title**: Use a clear, descriptive title for your pull request
2. **Description**: Fill out the pull request template with:
   - The purpose of the changes
   - Any issues addressed
   - How to test the changes
   - Screenshots if applicable
3. **Code Review**: Wait for code review from maintainers
4. **CI Checks**: Ensure all CI checks pass
5. **Approval**: Address feedback and wait for approval
6. **Merge**: A maintainer will merge your pull request

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for code style
- Use 4 spaces for indentation (no tabs)
- Use 88-character line limit (as per Black)
- Use snake_case for variables and function names
- Use CamelCase for class names

### Documentation

- Document all functions, classes, and modules using Google-style docstrings
- Keep documentation up-to-date with code changes
- Update the relevant section in the MkDocs documentation

Example docstring:
```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """Short description of the function.
    
    Longer description explaining what the function does in detail.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of the return value
        
    Raises:
        ExceptionType: Description of when this exception is raised
    """
```

### Testing

- Write tests for all new functionality
- Maintain or improve code coverage
- Structure tests to mirror the code being tested
- Use descriptive test names

## Working with Issues

### Finding Issues to Work On

- Check the "Issues" tab on GitHub
- Look for issues labeled "good first issue" for beginners
- Check the project roadmap for upcoming features

### Creating a New Issue

- Use the appropriate issue template
- Provide clear steps to reproduce bugs
- Include screenshots or examples if applicable
- Add relevant labels

### Issue Labels

- `bug`: Something isn't working
- `enhancement`: New features or improvements
- `documentation`: Documentation-related issues
- `good first issue`: Good for first-time contributors
- `help wanted`: Extra attention is needed

## Release Process

The release process is handled by the maintainers:

1. **Version Bump**: Update version numbers in:
   - `firm_capacity_analysis/__init__.py`
   - `setup.py`
   - Documentation files

2. **Changelog**: Update the CHANGELOG.md file

3. **Create Release Branch**:
   ```bash
   git checkout -b release/x.y.z develop
   ```

4. **Finalize Release**: Make any final adjustments

5. **Merge to Main**:
   ```bash
   git checkout main
   git merge --no-ff release/x.y.z
   git tag -a vx.y.z -m "Version x.y.z"
   ```

6. **Merge Back to Develop**:
   ```bash
   git checkout develop
   git merge --no-ff release/x.y.z
   ```

7. **Push Changes**:
   ```bash
   git push origin main
   git push origin develop
   git push --tags
   ```

## Community

### Communication Channels

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For general questions and discussions
- **Pull Requests**: For code contributions

### Code of Conduct

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md) to ensure a welcoming and inclusive environment. By participating, you are expected to uphold this code.

## Development Tips

### Working with Documentation

To build and view the documentation locally:

```bash
cd firm_capacity_analysis
pip install mkdocs mkdocs-material
mkdocs serve
```

Then visit http://127.0.0.1:8000/ in your browser.

### Working with the Desktop Application

To run the desktop application in development mode:

```bash
cd firm_capacity_analysis
python app.py
```

### Debugging

- Use logging instead of print statements
- Set breakpoints in your IDE
- Use the `pdb` module for interactive debugging:
  ```python
  import pdb; pdb.set_trace()
  ```

### Performance Profiling

For performance-critical code:

```bash
pip install cProfile
python -m cProfile -o profile.prof your_script.py
pip install snakeviz
snakeviz profile.prof
```

## Recognition

Contributors will be acknowledged in the project's:

- README.md
- CONTRIBUTORS.md file
- Release notes

## Thank You

Thank you for contributing to the Flexibility Analysis System! Your efforts help improve the project for everyone.