# Running the Flexibility Analysis System

This document provides a comprehensive reference for running the Flexibility Analysis System through various interfaces and with different options.

## Basic Usage

### Firm Capacity Analysis Only

To run basic firm capacity analysis without competitions:

```bash
# Run from the flex_270425 directory
python firm_capacity_analysis/src/main.py
```

This will:
1. Read configuration from `firm_capacity_analysis/config.yaml`
2. Process each substation defined in the configuration
3. Generate output plots and results in the specified output directory

### Firm Capacity with Competitions

To run the enhanced version that includes competition generation:

```bash
# Run from the flex_270425 directory
python firm_capacity_analysis/firm_capacity_with_competitions.py --competitions
```

## Command Line Options

The system supports several command-line options for customized operation:

| Option | Description | Example |
|--------|-------------|---------|
| `--config` | Path to config file | `--config path/to/config.yaml` |
| `--competitions` | Generate competitions | `--competitions` |
| `--schema` | Path to competition schema | `--schema path/to/schema.json` |
| `--year` | Target year for competition dates | `--year 2025` |
| `--targets` | Path to site-specific MWh targets | `--targets path/to/targets.csv` |

### Using Site-Specific Targets

To use custom energy targets for each substation:

```bash
python firm_capacity_analysis/firm_capacity_with_competitions.py --competitions --targets data/samples/site_targets.csv
```

The targets CSV file should have columns `site_name` and `target_mwh`.

### Setting a Target Year

To generate competitions for a specific year:

```bash
python firm_capacity_analysis/firm_capacity_with_competitions.py --competitions --year 2025
```

## Processing Parquet Files

For large datasets stored in parquet format:

```bash
python firm_capacity_analysis/firm_capacity_with_competitions.py --competitions --parquet data/raw/substations.parquet
```

Additional parquet processing options:

| Option | Description | Example |
|--------|-------------|---------|
| `--filter` | Filter network groups (comma-separated) | `--filter Monktonhall,Substation2` |
| `--workers` | Number of parallel workers | `--workers 4` |
| `--skip-existing` | Skip network groups with existing results | `--skip-existing` |

Example with all parquet options:

```bash
python firm_capacity_analysis/firm_capacity_with_competitions.py \
  --competitions \
  --parquet data/raw/substations.parquet \
  --filter Monktonhall \
  --workers 2 \
  --skip-existing \
  --targets data/samples/site_targets.csv \
  --year 2025
```

## Desktop Application

To run the desktop application:

```bash
# Run from the flex_270425 directory
python firm_capacity_analysis/app.py
```

Or use the packaged executable if available:

```bash
./FlexibilityAnalysisSystem.exe  # Windows
./FlexibilityAnalysisSystem      # macOS/Linux
```

## Test Commands

See the [TEST_COMMANDS.md](tests/TEST_COMMANDS.md) file for detailed testing commands.

## Output Structure

The system outputs results to the directory specified in the configuration file, typically:

```
output/
└── {substation}/
    ├── E_curve_plain.png         # Plain energy curve plot
    ├── E_curve_peak.png          # Peak-based energy curve plot
    ├── firm_capacity_results.csv # Tabular results
    ├── metadata.json             # Metadata in JSON format
    ├── competitions.json         # Generated competitions (if enabled)
    └── service_window_mwh.csv    # Service window MWh data (if generated)
```

## Configuration

The system is configured through `config.yaml` files. Key configuration sections include:

```yaml
input:
  demand_base_dir: "./data/samples/"
  in_substation_folder: false

output:
  base_dir: "./output"

firm_capacity:
  target_mwh: 300.0  # Target energy threshold
  tolerance: 0.01    # Bisection search tolerance

competitions:
  procurement_window_size_minutes: 30
  daily_service_periods: true
  financial_year: "2025/26"

substations:
  - name: substation1
    demand_file: "substation1.csv"
```

For full documentation, see the [detailed documentation](docs/index.md).