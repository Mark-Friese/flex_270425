# Testing Framework

This document explains the testing framework for the Flexibility Analysis System, including how to run tests, add new tests, and use the reference data system.

## Testing Architecture

The testing framework is built with pytest and follows a structured approach:

### Directory Structure

```
tests/
├── __init__.py               # Makes tests directory a proper package
├── conftest.py               # Shared pytest fixtures
├── copy_reference_data.py    # Creates reference data from output
├── data_review.py            # Generates data review reports
├── generate_service_window_mwh.py  # Extracts MWh data from service windows
├── make_reference_data.py    # Creates minimal reference data for testing
├── output/                   # Directory for test outputs
├── README.md                 # Testing documentation
├── reference_data/           # Reference data for comparison
│   └── Monktonhall/          # Substation-specific reference data
│       ├── competitions.json # Reference competition data
│       ├── metadata.json     # Reference metadata
│       └── firm_capacity_results.csv # Reference results
└── test_*.py                 # Individual test files
```

### Key Test Files

- **`test_firm_capacity.py`**: Tests for firm capacity calculations
- **`test_competitions.py`**: Tests for competition generation
- **`test_service_windows.py`**: Tests for service window generation
- **`test_basic.py`**: Basic tests to ensure the testing framework works
- **`test_ci_compatibility.py`**: Tests for CI/CD environment compatibility

### Reference Data System

The testing framework uses a reference data system to compare outputs against known good results:

1. **Reference Data**: Known good outputs stored in `tests/reference_data/`
2. **Test Outputs**: New outputs generated during tests stored in `output/`
3. **Comparison**: Tests compare new outputs against reference data

## Running Tests

### Basic Test Execution

To run all tests:

```bash
cd firm_capacity_analysis
python -m pytest
```

### Running Specific Tests

To run specific test files:

```bash
python -m pytest tests/test_firm_capacity.py
python -m pytest tests/test_competitions.py
python -m pytest tests/test_service_windows.py
```

To run tests matching a pattern:

```bash
python -m pytest -k "firm_capacity"
```

### Verbose Test Output

For more detailed output:

```bash
python -m pytest -v
```

To see print statements during tests:

```bash
python -m pytest -v -s
```

## Reference Data Management

### Creating Reference Data

Reference data can be created from existing outputs:

```bash
python tests/copy_reference_data.py --output-dir output --reference-dir tests/reference_data
```

This copies the following files for each substation:
- `firm_capacity_results.csv`
- `metadata.json`
- `competitions.json`
- `E_curve_plain.png`
- `E_curve_peak.png`

### Creating Minimal Reference Data

For CI/CD environments or fresh installations, minimal reference data can be created:

```bash
python tests/make_reference_data.py
```

This creates just enough reference data for tests to pass, with simplified content.

### Generating Service Window MWh Data

To extract and verify MWh data from service windows:

```bash
python tests/generate_service_window_mwh.py --substations Monktonhall
```

This creates a CSV file with detailed MWh information for each service window.

## Data Review Reports

To generate reports comparing reference data with new outputs:

```bash
python tests/data_review.py --substations Monktonhall
```

This creates:
- HTML report with highlighted differences
- CSV file with metric comparisons
- JSON file with raw comparison data

## Pytest Fixtures

The testing framework uses pytest fixtures to share common testing resources:

```python
@pytest.fixture(scope="session")
def reference_dir():
    """Path to reference data directory."""
    return Path("tests/reference_data")

@pytest.fixture(scope="session")
def output_dir():
    """Path to output data directory."""
    return Path("output")

@pytest.fixture(scope="session")
def substations():
    """List of substations to test."""
    return ["Monktonhall"]  # Update with your substation names

@pytest.fixture(scope="session")
def reference_competitions(reference_dir, substations):
    """Load reference competition data for all substations."""
    competitions = {}
    for sub in substations:
        comp_path = reference_dir / sub / "competitions.json"
        if comp_path.exists():
            with open(comp_path) as f:
                competitions[sub] = json.load(f)
        else:
            competitions[sub] = None
    return competitions
```

## Test Types

The testing framework includes several types of tests:

### Unit Tests

Test individual functions and components:

```python
def test_energy_above_capacity():
    """Test energy_above_capacity function."""
    demand = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    capacity = 3.0
    delta_t = 0.5
    
    result = energy_above_capacity(demand, capacity, delta_t)
    expected = (0.0 + 0.0 + 0.0 + 1.0 + 2.0) * 0.5
    
    assert result == expected
```

### Integration Tests

Test the interaction between multiple components:

```python
def test_firm_capacity_calculation_integration():
    """Test firm capacity calculation with real data."""
    # Load test data
    df = pd.read_csv("tests/data/test_demand.csv")
    
    # Calculate firm capacity
    demand = df["Demand (MW)"].values
    target_mwh = 100.0
    
    c_plain = invert_capacity(energy_above_capacity, demand, target_mwh)
    c_peak = invert_capacity(energy_peak_based, demand, target_mwh)
    
    # Check results are within expected range
    assert 10.0 <= c_plain <= 15.0
    assert 10.0 <= c_peak <= 15.0
```

### Comparison Tests

Compare new outputs with reference data:

```python
def test_firm_capacity_values(reference_metadata, new_metadata):
    """Test that firm capacity values are consistent with reference data."""
    for sub in reference_metadata:
        # Load reference and new metadata
        ref_meta = reference_metadata[sub]
        new_meta = new_metadata[sub]
        
        # Check firm capacity values
        assert abs(ref_meta["C_plain_MW"] - new_meta["C_plain_MW"]) < 0.001
        assert abs(ref_meta["C_peak_MW"] - new_meta["C_peak_MW"]) < 0.001
```

### Compatibility Tests

Check compatibility with different environments:

```python
def test_cross_platform_compatibility():
    """Test for potential cross-platform compatibility issues."""
    # Check for presence of files that might have platform-specific issues
    test_files = [
        Path("pytest.ini"),
        Path("tests/__init__.py")
    ]
    
    for file_path in test_files:
        if file_path.exists():
            # Check for Windows-specific line endings in text files
            with open(file_path, 'rb') as f:
                content = f.read()
                # Count Windows line endings
                crlf_count = content.count(b'\r\n')
                # Count Unix line endings
                lf_count = content.count(b'\n') - crlf_count
                
                # If file has mixed line endings, it could cause issues
                assert not (crlf_count > 0 and lf_count > 0)
```

## CI/CD Integration

The testing framework is integrated with GitHub Actions for automated testing:

### GitHub Actions Workflow

The workflow is defined in `.github/workflows/test-flexibility-analysis.yml`:

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
```

### Cross-Platform Testing

The testing framework includes compatibility checks for different platforms:

- **Line Endings**: Check for mixed line endings that could cause issues
- **Path Separators**: Use `Path` objects from `pathlib` for cross-platform paths
- **Dependencies**: Platform-specific dependencies are handled in installation scripts

## Adding New Tests

To add new tests to the framework:

### 1. Create a Test File

Create a new file named `test_*.py` in the `tests` directory:

```python
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Import the functions to test
from src.calculations import energy_above_capacity

def test_new_feature():
    """Test description."""
    # Test implementation
    assert True  # Replace with actual assertions
```

### 2. Use Fixtures

Use existing fixtures or create new ones in `conftest.py`:

```python
@pytest.fixture
def test_data():
    """Create test data for the new feature."""
    return {
        'param1': 'value1',
        'param2': 'value2'
    }

def test_with_fixture(test_data):
    """Test using the fixture."""
    assert test_data['param1'] == 'value1'
```

### 3. Add Reference Data

If the test compares with reference data, add the necessary files to `tests/reference_data/` or update the `make_reference_data.py` script.

### 4. Use Test Parameterization

For tests with multiple similar cases, use pytest parameterization:

```python
@pytest.mark.parametrize("input_value,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double_function(input_value, expected):
    """Test that the function doubles the input."""
    result = double(input_value)
    assert result == expected
```

## Performance Testing

For performance testing of critical functions:

```python
def test_energy_calculation_performance():
    """Test performance of energy calculation functions."""
    # Generate large test data
    demand = np.random.rand(100_000) * 10.0
    capacity = 5.0
    
    # Measure execution time
    start_time = time.time()
    energy_above_capacity(demand, capacity)
    plain_time = time.time() - start_time
    
    start_time = time.time()
    energy_peak_based(demand, capacity)
    peak_time = time.time() - start_time
    
    print(f"Plain method: {plain_time:.4f}s, Peak method: {peak_time:.4f}s")
    
    # Assert that execution time is within acceptable limits
    assert plain_time < 0.1  # Should be very fast
    assert peak_time < 1.0   # Slower due to segment processing
```

## Test Coverage

To measure test coverage:

```bash
pip install pytest-cov
python -m pytest --cov=src tests/
```

To generate a coverage report:

```bash
python -m pytest --cov=src --cov-report=html tests/
```

## Best Practices

When writing tests:

1. **Test in isolation**: Each test should be independent and not rely on the state from other tests
2. **Use meaningful names**: Test names should describe what they're testing
3. **Use assertions effectively**: Be specific about what you're checking
4. **Add docstrings**: Explain what each test is checking
5. **Test edge cases**: Include tests for boundary conditions and error cases
6. **Keep tests fast**: Optimize tests to run quickly
7. **Avoid hard-coded paths**: Use fixtures and relative paths
8. **Use parameterization**: For testing multiple similar cases
9. **Mock external dependencies**: Use `unittest.mock` or `pytest-mock` for external services

## Troubleshooting Tests

### Missing Reference Data

If tests fail due to missing reference data:

```bash
python tests/make_reference_data.py
```

### Test Discovery Issues

If pytest can't find your tests:
1. Ensure test files start with `test_`
2. Ensure test functions start with `test_`
3. Check that `__init__.py` exists in the test directory
4. Verify the pytest configuration in `pytest.ini`

### Data Loading Issues

If tests can't load data:
1. Check file paths and permissions
2. Ensure reference data exists
3. Verify column names and data formats