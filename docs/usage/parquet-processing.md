# Parquet Processing Guide

This guide explains how to use the Flexibility Analysis System with Parquet files, which are particularly useful for large datasets.

## What is Parquet?

Apache Parquet is a columnar storage file format designed for efficient data storage and retrieval. Benefits include:

- Improved compression and encoding schemes
- Efficient querying of specific columns
- Reduced I/O operations for large datasets
- Better handling of complex nested data structures

## When to Use Parquet

Consider using Parquet files when:

- Working with large datasets (>100MB)
- Processing multiple substations in a single file
- Dealing with high-resolution time series data
- Needing faster data loading and filtering

## Requirements for Parquet Processing

To work with Parquet files, you need:

1. The `pyarrow` package installed:
   ```bash
   pip install pyarrow
   ```

2. Optional but recommended, the `dask` package for larger-than-memory processing:
   ```bash
   pip install "dask[complete]"
   ```

3. Properly formatted Parquet files with:
   - A `Timestamp` column (or mappable column)
   - A `Demand (MW)` column (or mappable column)
   - A `Network Group Name` column for identifying substations

## Command Line Usage

To process Parquet files from the command line:

```bash
python firm_capacity_with_competitions.py --parquet data/raw/substations.parquet --competitions
```

### Additional Parquet Processing Options

| Option | Description | Example |
|--------|-------------|---------|
| `--filter` | Process only specific network groups | `--filter Monktonhall,Substation2` |
| `--workers` | Number of parallel workers | `--workers 4` |
| `--skip-existing` | Skip network groups with existing results | `--skip-existing` |

Example with all options:

```bash
python firm_capacity_with_competitions.py \
  --parquet data/raw/substations.parquet \
  --filter Monktonhall,Substation2 \
  --workers 4 \
  --skip-existing \
  --competitions \
  --year 2025
```

## Parquet File Structure

The system expects Parquet files with the following structure:

### Required Columns

| Column | Description | Mapping |
|--------|-------------|---------|
| `Timestamp` or mappable | Date and time of each data point | Can be mapped from `timestamp`, `time`, etc. |
| `Demand (MW)` or mappable | Power demand in megawatts | Can be mapped from `demand_mw`, `power`, etc. |
| `Network Group Name` or mappable | Identifier for the substation or network group | Can be mapped from `group_name`, `network_group`, etc. |

### Column Mapping

The system supports column mapping to accommodate different naming conventions:

```python
COLUMN_MAPPINGS = {
    'group_name': 'Network Group Name',
    'timestamp': 'Timestamp',
    'network_group': 'Network Group Name',
    'demand_mw': 'Demand (MW)',
    'underlying_demand_mw': 'Demand (MW)',
}
```

When loading a Parquet file, the system will automatically map columns based on this dictionary.

## Parallel Processing

When working with large Parquet files containing multiple network groups, the system can process them in parallel:

```bash
python firm_capacity_with_competitions.py --parquet data/raw/substations.parquet --workers 4
```

The `--workers` parameter specifies the number of parallel processes to use. Consider the following when choosing this value:

- Set to the number of CPU cores for optimal performance
- Reduce for memory-constrained systems
- Increase for I/O-bound operations

## Filtering Network Groups

To process only specific network groups from a Parquet file:

```bash
python firm_capacity_with_competitions.py --parquet data/raw/substations.parquet --filter Monktonhall,Substation2
```

This is particularly useful for:
- Testing with a subset of network groups
- Processing high-priority groups first
- Dividing large files into manageable batches

## Skipping Existing Results

To avoid reprocessing network groups that already have results:

```bash
python firm_capacity_with_competitions.py --parquet data/raw/substations.parquet --skip-existing
```

This option checks for the existence of `firm_capacity_results.csv` in the output directory for each network group and skips processing if found.

## Output Structure

Parquet processing generates the same output structure as CSV processing:

```
output/
└── {network_group}/
    ├── E_curve_plain.png         # Plain energy curve plot
    ├── E_curve_peak.png          # Peak-based energy curve plot
    ├── firm_capacity_results.csv # Tabular results
    ├── metadata.json             # Metadata in JSON format
    ├── competitions.json         # Generated competitions (if enabled)
    └── service_window_mwh.csv    # Service window MWh data (if generated)
```

Additionally, a summary file is created:

```
output/parquet_summary.csv  # Summary of all processed network groups
```

This summary includes:
- Processing status (success, error, skipped)
- Firm capacity results
- Processing time
- Row counts
- Error messages (if applicable)

## Creating Parquet Files

You can convert CSV files to Parquet format using pandas:

```python
import pandas as pd

# Read CSV files
df = pd.read_csv('data/samples/substation1.csv')

# Add network group column if missing
df['Network Group Name'] = 'Substation1'

# Convert to Parquet
df.to_parquet('data/raw/substation1.parquet')
```

For multiple CSV files:

```python
import pandas as pd
import glob
import os

# Create empty list to store dataframes
dfs = []

# Read all CSV files
for csv_file in glob.glob('data/samples/*.csv'):
    # Read CSV
    df = pd.read_csv(csv_file)
    
    # Add network group name based on filename
    network_group = os.path.basename(csv_file).replace('.csv', '')
    df['Network Group Name'] = network_group
    
    # Add to list
    dfs.append(df)

# Combine all dataframes
combined_df = pd.concat(dfs, ignore_index=True)

# Write to Parquet
combined_df.to_parquet('data/raw/all_substations.parquet')
```

## Memory Optimization Techniques

When working with large Parquet files:

### Using Dask for Larger-than-Memory Processing

```python
import dask.dataframe as dd

# Read Parquet file using Dask
ddf = dd.read_parquet('data/raw/large_file.parquet')

# Filter for specific network group
group_ddf = ddf[ddf['Network Group Name'] == 'Monktonhall']

# Convert to pandas for analysis
df = group_ddf.compute()
```

### Chunk-Based Processing

```python
import pyarrow.parquet as pq
import pandas as pd

# Open Parquet file
parquet_file = pq.ParquetFile('data/raw/large_file.parquet')

# Identify unique network groups
unique_groups = set()
for batch in parquet_file.iter_batches():
    df_batch = batch.to_pandas()
    unique_groups.update(df_batch['Network Group Name'].unique())

print(f"Found {len(unique_groups)} unique network groups")
```

## Examples

### Example 1: Basic Parquet Processing

```bash
python firm_capacity_with_competitions.py --parquet data/raw/substations.parquet --competitions
```

### Example 2: Parallel Processing with Filtering

```bash
python firm_capacity_with_competitions.py \
  --parquet data/raw/substations.parquet \
  --filter Monktonhall,Substation2 \
  --workers 4 \
  --competitions
```

### Example 3: Incremental Processing

```bash
# First run - process half the substations
python firm_capacity_with_competitions.py \
  --parquet data/raw/substations.parquet \
  --filter "Group1,Group2,Group3" \
  --competitions

# Second run - process the rest with skip-existing
python firm_capacity_with_competitions.py \
  --parquet data/raw/substations.parquet \
  --skip-existing \
  --competitions
```

## Performance Considerations

- **Memory Usage**: Monitoring memory usage is important, especially with large files
- **Processing Time**: Parallel processing can significantly reduce processing time
- **File Size**: Parquet files are typically 2-4x smaller than equivalent CSVs
- **Filtering Efficiency**: Parquet's columnar format makes filtering very efficient