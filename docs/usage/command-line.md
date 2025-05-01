# Command Line Interface

The Flexibility Analysis System provides a comprehensive command-line interface (CLI) that allows you to run analyses, generate competitions, and process various data formats. This guide covers all available commands and options.

## Available Scripts

The system provides two main entry points:

1. **`src/main.py`**: Basic firm capacity analysis without competition generation
2. **`firm_capacity_with_competitions.py`**: Enhanced version with competition generation and additional features

## Basic Firm Capacity Analysis

To run basic firm capacity analysis:

```bash
# From the flex_270425 directory
python firm_capacity_analysis/src/main.py
```

This will:
1. Load configuration from `config.yaml`
2. Process each substation defined in the configuration
3. Calculate firm capacity using both methods (standard and peak-based)
4. Generate plots and result files

## Firm Capacity with Competitions

To run the enhanced version with competition generation:

```bash
python firm_capacity_analysis/firm_capacity_with_competitions.py --competitions
```

## Common Options

Both scripts support these options:

| Option | Description | Example |
|--------|-------------|---------|
| `--config` | Path to config file | `--config custom_config.yaml` |

## Competition Generation Options

The `firm_capacity_with_competitions.py` script supports these additional options:

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--competitions` | Enable competition generation | Disabled | `--competitions` |
| `--schema` | Path to competition schema | None | `--schema schema.json` |
| `--year` | Target year for competition dates | Current year | `--year 2025` |
| `--targets` | Path to site-specific MWh targets | None | `--targets targets.csv` |

## Parquet Data Processing

For processing data stored in parquet format:

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--parquet` | Path to parquet file | None | `--parquet data.parquet` |
| `--filter` | Filter network groups (comma-separated) | All groups | `--filter Monktonhall,Station2` |
| `--workers` | Number of parallel workers | 4 | `--workers 2` |
| `--skip-existing` | Skip groups with existing results | Disabled | `--skip-existing` |

## Examples

### Basic Analysis

```bash
python firm_capacity_analysis/src/main.py --config my_config.yaml
```

### Competition Generation

```bash
python firm_capacity_analysis/firm_capacity_with_competitions.py --competitions --year 2025
```

### Parquet Processing with Site-Specific Targets

```bash
python firm_capacity_analysis/firm_capacity_with_competitions.py \
  --competitions \
  --parquet data/raw/demand_data.parquet \
  --filter Monktonhall \
  --workers 2 \
  --skip-existing \
  --targets data/samples/site_targets.csv \
  --year 2025
```

## Input Data Formats

### CSV Format

CSV files should have at minimum:
- `Timestamp` column with datetime values
- `Demand (MW)` column with demand values

Example:
```csv
Timestamp,Demand (MW)
2023-01-01 00:00:00,12.34
2023-01-01 00:30:00,11.56
...
```

### Parquet Format

Parquet files should include:
- `Timestamp` column or equivalent (will be mapped if named differently)
- `Demand (MW)` or equivalent demand column
- `Network Group Name` or equivalent for identifying substations

## Site-specific Targets CSV

The targets CSV file should have:
- `site_name` column matching substation names
- `target_mwh` column with target energy values

Example:
```csv
site_name,target_mwh
Monktonhall,150
Substation2,200
```

## Output Files

The system generates these output files in the configured output directory:

| File | Description |
|------|-------------|
| `E_curve_plain.png` | Plot of standard energy curve |
| `E_curve_peak.png` | Plot of peak-based energy curve |
| `firm_capacity_results.csv` | Summary of firm capacity results |
| `metadata.json` | Detailed analysis metadata |
| `competitions.json` | Generated competitions (if enabled) |
| `service_window_mwh.csv` | Service window MWh data (if generated) |

## Return Codes

The scripts return standard exit codes:
- `0`: Success
- Non-zero: Error occurred

## Logging

The system logs information to both stdout and log files:
- Console output includes status updates and errors
- Detailed logs are written to log files in the project directory

You can adjust log verbosity by modifying the logging configuration in the code.

## Troubleshooting

If you encounter issues:

1. **Configuration Issues**: Verify your config.yaml file is correct
2. **Data Format Issues**: Ensure your data files match the expected format
3. **Schema Validation Errors**: Check competition schema compatibility
4. **Memory Issues**: For large parquet files, reduce the number of workers
5. **Permission Issues**: Ensure write access to the output directory

For more help, refer to the [FAQ](../reference/faq.md) or [submit an issue](https://github.com/yourusername/flex_270425/issues).