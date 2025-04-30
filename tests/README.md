# Flexibility Analysis Testing Framework

This directory contains tests and utilities for the Flexibility Analysis system to ensure code changes do not create unintended consequences.

## Test Structure

The testing framework is built with pytest and follows a standard structure:

- `conftest.py`: Contains pytest fixtures and shared test utilities
- `__init__.py`: Makes this directory a proper Python package
- `make_reference_data.py`: Script to generate minimal reference data for testing
- Individual test files targeting specific functionality:
  - `test_firm_capacity.py`: Tests for firm capacity calculations
  - `test_competitions.py`: Tests for competition generation
  - `test_service_windows.py`: Tests for service window generation

## Running Tests

To run the tests locally:

```bash
cd firm_capacity_analysis
python -m pytest -v tests/
```

To run specific test files:

```bash
python -m pytest -v tests/test_firm_capacity.py
python -m pytest -v tests/test_competitions.py
python -m pytest -v tests/test_service_windows.py
```

## Reference Data

The tests rely on reference data stored in the `tests/reference_data` directory. This data includes:

- `competitions.json`: Reference competition data
- `metadata.json`: Reference metadata for firm capacity analysis
- `firm_capacity_results.csv`: Reference firm capacity results

If reference data is missing, the `make_reference_data.py` script will generate minimal reference data for testing.

## CI/CD Integration

The tests are automatically run in GitHub Actions on push to main/develop branches or on pull requests. The workflow is defined in `.github/workflows/test-flexibility-analysis.yml`.

## Troubleshooting

If tests are failing due to missing reference data, you can regenerate it:

```bash
cd firm_capacity_analysis
python tests/make_reference_data.py
```

If pytest cannot discover the tests, verify:
1. You have `__init__.py` files in all test directories
2. Test files follow the naming convention `test_*.py`
3. Test classes are named with the suffix `Test`
4. Test functions are named with the prefix `test_`
