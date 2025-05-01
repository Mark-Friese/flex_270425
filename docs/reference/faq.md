# Frequently Asked Questions

This page provides answers to frequently asked questions about the Flexibility Analysis System.

## General Questions

### What is the Flexibility Analysis System?

The Flexibility Analysis System is a comprehensive toolkit for analyzing power network demand data and generating flexibility service competitions. It helps network operators identify flexibility needs in power networks by analyzing historical demand data to determine firm capacity requirements and generating standardized flexibility competition specifications.

### What are the key features of the system?

The key features include:
- Firm capacity analysis using both standard and peak-based approaches
- Automated service window identification
- Standardized competition generation
- Support for both CSV and Parquet data formats
- User-friendly desktop application

## Technical Questions

### What is firm capacity?

Firm capacity represents the level of demand that can be reliably served at all times. It is the threshold above which flexibility services may be needed to manage demand peaks.

### How is firm capacity calculated?

The system implements two methods for calculating firm capacity:
1. Energy Above Capacity (Plain Method): Sums all energy that exceeds the capacity threshold over the entire time period
2. Peak-Based Energy Above Capacity: Identifies contiguous segments where demand exceeds capacity, then uses the peak demand within each segment for the calculation

### What are service windows?

Service windows are specific time periods (e.g., "Monday 17:00-19:30") when demand is expected to exceed firm capacity and flexibility services may be required. They define when, how much, and for how long flexibility is needed.

## Usage Questions

### What data format does the system support?

The system supports both CSV and Parquet data formats. CSV files should have at minimum:
- `Timestamp` column with datetime values
- `Demand (MW)` column with demand values

### How do I generate competitions?

To generate competitions, use the `--competitions` flag with the main script:
```bash
python firm_capacity_with_competitions.py --competitions
```

### Can I customize the target energy threshold?

Yes, you can set the target energy threshold in the configuration file:
```yaml
firm_capacity:
  target_mwh: 300.0  # Set your desired value here
```

You can also use site-specific targets via a CSV file:
```bash
python firm_capacity_with_competitions.py --targets data/samples/site_targets.csv
```

## Troubleshooting

### The system can't find my data files

Ensure your data files are in the correct location as specified in your configuration. By default, the system looks for files at `{demand_base_dir}/{substation_name}.csv`.

### Error in firm capacity calculation

This can happen if:
- Your data has invalid values (NaN, infinity, etc.)
- Target energy threshold is too high relative to the data
- Tolerance is too tight for the bisection search

Try adjusting the `target_mwh` and `tolerance` parameters in your configuration.

### The desktop application won't start

Ensure you have all required dependencies installed:
```bash
pip install -r requirements.txt
pip install -r packaging_requirements.txt
```

On Linux, ensure you have the required system libraries:
```bash
# For Debian/Ubuntu
sudo apt-get install libgtk-3-0 libwebkit2gtk-4.0-37
```