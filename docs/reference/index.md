# Reference Documentation

This section provides detailed reference information for the Flexibility Analysis System, including API references, configuration options, and terminology.

## API Reference

The [API Reference](api-reference.md) documents the public functions and classes available for extending or integrating with the Flexibility Analysis System.

## Configuration Reference

The [Configuration Reference](configuration-reference.md) provides detailed information on all configuration options available in the system.

## Glossary

The [Glossary](glossary.md) defines key terms and concepts used throughout the documentation and codebase.

## Key Reference Topics

### Configuration Files

The system uses YAML configuration files for various settings:

```yaml
input:
  demand_base_dir: "./data/samples/"
  in_substation_folder: false

output:
  base_dir: "./output"

firm_capacity:
  target_mwh: 300.0
  tolerance: 0.01

competitions:
  procurement_window_size_minutes: 30
  daily_service_periods: true
  financial_year: "2025/26"

substations:
  - name: substation1
    demand_file: "substation1.csv"
```

### Command-Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--config` | Path to config file | `--config path/to/config.yaml` |
| `--competitions` | Generate competitions | `--competitions` |
| `--schema` | Path to competition schema | `--schema path/to/schema.json` |
| `--year` | Target year for competition dates | `--year 2025` |
| `--targets` | Path to site-specific MWh targets | `--targets path/to/targets.csv` |
| `--parquet` | Path to parquet file | `--parquet data.parquet` |
| `--filter` | Filter network groups | `--filter Monktonhall,Station2` |
| `--workers` | Number of parallel workers | `--workers 4` |
| `--skip-existing` | Skip existing results | `--skip-existing` |

### Output Files

| File | Description |
|------|-------------|
| `E_curve_plain.png` | Plot of standard energy curve |
| `E_curve_peak.png` | Plot of peak-based energy curve |
| `firm_capacity_results.csv` | Summary of firm capacity results |
| `metadata.json` | Detailed analysis metadata |
| `competitions.json` | Generated competitions |
| `service_window_mwh.csv` | Service window MWh data |

### Important Functions

| Function | Description |
|----------|-------------|
| `energy_above_capacity()` | Calculate energy above capacity |
| `energy_peak_based()` | Calculate peak-based energy above capacity |
| `invert_capacity()` | Find capacity for a target energy |
| `find_overload_segments()` | Identify segments where demand exceeds capacity |
| `create_service_window_from_segment()` | Convert a segment to a service window |
| `generate_competition_service_periods()` | Generate service periods from demand data |
| `create_competitions_from_df()` | Generate competitions from demand data |

For comprehensive information on these and other topics, refer to the specific reference sections.