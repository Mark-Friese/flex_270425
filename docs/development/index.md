# Developer Guide

This guide provides information for developers who want to contribute to the Flexibility Analysis System or extend its functionality.

## Getting Started

Before you begin development:

1. **Set up a development environment**:
   ```bash
   git clone https://github.com/yourusername/flex_270425.git
   cd flex_270425
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r firm_capacity_analysis/requirements-test.txt
   ```

2. **Understand the architecture**:
   - Read the [Technical Documentation](../technical/index.md)
   - Review the [Code Structure](code-structure.md)

## Development Standards

### Coding Standards

- Follow PEP 8 for Python code style
- Use type hints for better IDE support and static analysis
- Write comprehensive docstrings using Google-style docstring format
- Keep functions focused on a single responsibility
- Unit test all new functionality

### Documentation Standards

- Update user documentation for new features
- Include mathematical explanations for algorithms
- Add examples for new command-line options
- Document configuration options

### Git Workflow

We follow a standard Git workflow:

1. Create a feature branch from `develop` branch
2. Make your changes with descriptive commit messages
3. Add tests for new functionality
4. Submit a pull request to the `develop` branch
5. Address any feedback from code review
6. Once approved, your PR will be merged

## Testing

The project uses pytest for testing:

```bash
# Run all tests
python -m pytest

# Run specific tests
python -m pytest tests/test_firm_capacity.py

# Run with coverage
python -m pytest --cov=src tests/
```

See the [Testing Framework](testing.md) documentation for more details.

## CI/CD

The project uses GitHub Actions for continuous integration:

- Automated tests run on PR submissions
- Code quality checks using flake8 and mypy
- Documentation builds using MkDocs

See the [CI/CD Integration](ci-cd.md) documentation for more details.

## Common Development Tasks

### Adding New Command-Line Options

1. Update the argument parser in `firm_capacity_with_competitions.py`
2. Add handling for the new option in the appropriate function
3. Update the documentation in `docs/usage/command-line.md`
4. Add tests to verify the option works correctly

### Extending Competition Generation

1. Understand the existing code in `competition_builder.py`
2. Make your changes to add new functionality
3. Update the schema if necessary
4. Add tests for the new functionality
5. Update documentation

### Improving Visualization

1. Modify the plotting functions in `plotting.py`
2. Follow visualization best practices (clear labels, appropriate colors, etc.)
3. Ensure accessibility for color-blind users
4. Test with various data sets

## Building Documentation

To build the documentation:

```bash
cd firm_capacity_analysis
pip install mkdocs mkdocs-material
mkdocs build
```

Or to serve it locally:

```bash
mkdocs serve
```

See the [Contributing](contribution.md) guide for more information on how to contribute to the project.