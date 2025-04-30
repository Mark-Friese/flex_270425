# Flexibility Analysis Testing - Command Reference

This document provides quick reference commands for running the testing framework.

## Creating Reference Datasets

```bash
# Create reference data from current outputs
python tests/copy_reference_data.py --output-dir "C:\Users\mfrie\Projects\flexibility\flex_270425\firm_capacity_analysis\output" --reference-dir "C:\Users\mfrie\Projects\flexibility\flex_270425\firm_capacity_analysis\tests\reference_data"

# For relative paths (running from firm_capacity_analysis directory)
python tests/copy_reference_data.py --output-dir output --reference-dir tests/reference_data
```

## Generating Service Window MWh Data

```bash
# Generate MWh data for Monktonhall
python tests/generate_service_window_mwh.py --substations Monktonhall --output-dir "C:\Users\mfrie\Projects\flexibility\flex_270425\firm_capacity_analysis\output"

# For relative paths (running from firm_capacity_analysis directory)
python tests/generate_service_window_mwh.py --substations Monktonhall
```

## Running Tests

```bash
# Run all tests
cd firm_capacity_analysis
python -m pytest tests/

# Run specific test files
python -m pytest tests/test_firm_capacity.py
python -m pytest tests/test_competitions.py
python -m pytest tests/test_service_windows.py

# Run with verbose output
python -m pytest -v tests/

# Run and show print output
python -m pytest -v tests/ -s
```

## Data Review

```bash
# Generate data review reports
python tests/data_review.py --substations Monktonhall --reference-dir "C:\Users\mfrie\Projects\flexibility\flex_270425\firm_capacity_analysis\tests\reference_data" --output-dir "C:\Users\mfrie\Projects\flexibility\flex_270425\firm_capacity_analysis\output" --report-dir "C:\Users\mfrie\Projects\flexibility\flex_270425\firm_capacity_analysis\reports"

# For relative paths (running from firm_capacity_analysis directory)
python tests/data_review.py --substations Monktonhall
```

## Regenerating Outputs

```bash
# Generate outputs with specific parameters
python firm_capacity_with_competitions.py --competitions --parquet data\raw\monktonhall.parquet --workers 1 --targets data\samples\site_targets.csv --filter Monktonhall --year 2025
```

## Installing Required Packages

```bash
# Install required packages
pip install pytest pandas numpy matplotlib pyyaml
```