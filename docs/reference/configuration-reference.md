# Configuration Reference

This document provides a detailed reference for all configuration options in the Flexibility Analysis System.

## Configuration File Format

The system uses YAML configuration files with the following main sections:

- `input`: Input data configuration
- `output`: Output directory configuration
- `firm_capacity`: Firm capacity calculation parameters
- `competitions`: Competition generation parameters
- `substations`: List of substations to process

Example configuration file:

```yaml
input:
  demand_base_dir: "./data/samples/"
  in_substation_folder: false
  metadata_file: "./data/metadata.csv"

output:
  base_dir: "./output"

firm_capacity:
  target_mwh: 300.0
  tolerance: 0.01

competitions:
  procurement_window_size_minutes: 30
  disaggregate_days: true
  daily_service_periods: true
  financial_year: "2025/26"

substations:
  - name: "substation1"
    demand_file: "substation1.csv"
  - name: "substation2"
    demand_file: "substation2.csv"
```

## Input Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `demand_base_dir` | string | `"./data/samples/"` | Base directory for demand data files |
| `in_substation_folder` | boolean | `false` | Whether data is in substation-specific folders |
| `metadata_file` | string | `null` | Optional metadata file with additional substation information |

### Data Location Logic

The system uses the following logic to locate demand data files:

When `in_substation_folder` is `false` (default):
- The system looks for files at `{demand_base_dir}/{substation_name}.csv`
- Example: `./data/samples/substation1.csv`

When `in_substation_folder` is `true`:
- The system looks for files at `{output_base_dir}/{substation_name}/{demand_file}`
- Example: `./output/substation1/demand.csv`

## Output Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_dir` | string | `"./output"` | Directory where output files will be created |

### Output Directory Structure

The system creates the following directory structure for outputs:

```
{base_dir}/
└── {substation_name}/
    ├── E_curve_plain.png         # Plot for plain E(C) curve
    ├── E_curve_peak.png          # Plot for peak-based E(C) curve
    ├── firm_capacity_results.csv # Tabular results
    ├── metadata.json             # Metadata in JSON format
    ├── competitions.json         # Generated competitions (if enabled)
    └── service_window_mwh.csv    # Service window MWh data (if generated)
```

## Firm Capacity Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `target_mwh` | float | `300.0` | Target energy threshold in MWh for firm capacity inversion |
| `tolerance` | float | `0.01` | Tolerance for bisection search (relative to maximum demand) |

### Target MWh Impact

The `target_mwh` parameter significantly impacts the calculated firm capacity:
- Higher values result in lower firm capacity
- Lower values result in higher firm capacity

The target represents the amount of energy (in MWh) that would need to be provided by flexibility services over the analysis period.

## Competition Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `procurement_window_size_minutes` | integer | `30` | Size of individual service windows in minutes |
| `disaggregate_days` | boolean | `false` | Whether to create separate windows for each day of week |
| `daily_service_periods` | boolean | `false` | Group windows by day instead of by month |
| `financial_year` | string | `null` | Financial year for competition dates (format: "YYYY/YY") |

### Procurement Window Size Impact

The `procurement_window_size_minutes` parameter affects the granularity of service windows:
- Smaller values (e.g., 30 minutes) create more, shorter windows
- Larger values (e.g., 120 minutes) create fewer, longer windows

This parameter should be set to a multiple of the time step in the demand data (typically 30 minutes).

### Service Period Grouping

The `daily_service_periods` parameter determines how service windows are grouped:

When `false` (default):
- Service windows are grouped by month
- Each month with overloads gets a service period
- Period name format: "January"

When `true`:
- Service windows are grouped by specific day
- Each day with overloads gets a service period
- Period name format: "January 15 (Monday)"

### Financial Year Format

The `financial_year` parameter should be in the format "YYYY/YY":
- Example: "2025/26" for April 2025 to March 2026

This parameter is used to generate competition dates aligned with financial year planning cycles.

## Substations Configuration

The `substations` section is a list of substation configurations:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Substation name (used for folder and competition naming) |
| `demand_file` | string | Conditional | Name of the demand data file (required if `in_substation_folder` is true) |

Each substation entry must have at least a `name` attribute:

```yaml
substations:
  - name: "substation1"  # Minimum required
  - name: "substation2"
    demand_file: "substation2.csv"  # Optional if in_substation_folder is false
```

## Command Line Overrides

Some configuration options can be overridden via command-line parameters:

| Command Line Parameter | Overrides Configuration |
|------------------------|-------------------------|
| `--config` | Path to config file |
| `--competitions` | Enables competition generation |
| `--year` | Target year for competition dates |
| `--targets` | Path to site-specific MWh targets |
| `--schema` | Path to competition schema for validation |

Example:
```bash
python firm_capacity_with_competitions.py --config custom_config.yaml --competitions --year 2025
```

## Site-Specific Targets File

The site-specific targets file should be a CSV with at least two columns:

```csv
site_name,target_mwh
substation1,150
substation2,200
```

| Column | Description |
|--------|-------------|
| `site_name` | Substation name (must match the name in configuration) |
| `target_mwh` | Target energy threshold in MWh |

## Optional Field Configuration

The system supports different configuration modes for optional fields in competitions:

### Root-Level Optional Fields

| Field | Description | Default | Configuration Mode |
|-------|-------------|---------|-------------------|
| `contact` | Email for communications | "flexibility@example.com" | STANDARD, CUSTOM |
| `archive_on` | Archive date | 7 days after bidding closes | STANDARD, CUSTOM |
| `dps_record_reference` | DPS record reference | f"flex_{reference.lower()}" | STANDARD, CUSTOM |
| `product_type` | Product type | "Scheduled Utilisation" | STANDARD, CUSTOM |
| `minimum_connection_voltage` | Min voltage in KV | Based on nominal_voltage or "0.24" | REQUIRED_ONLY, STANDARD, CUSTOM |
| `maximum_connection_voltage` | Max voltage in KV | Based on nominal_voltage or "33" | REQUIRED_ONLY, STANDARD, CUSTOM |
| `minimum_budget` | Min budget in £ | "5000.00" | CUSTOM |
| `maximum_budget` | Max budget in £ | "10000.00" | CUSTOM |
| `availability_guide_price` | Guide price for availability | "10.00" | CUSTOM |
| `utilisation_guide_price` | Guide price for utilisation | "240" | CUSTOM |
| `service_fee` | Annual fee for capacity | "9.45" | CUSTOM |
| `pricing_type` | Price determination method | "auction" | CUSTOM |

### Service Window-Level Optional Fields

| Field | Description | Default | Configuration Mode |
|-------|-------------|---------|-------------------|
| `public_holiday_handling` | Holiday designation | Not set | STANDARD, CUSTOM |
| `minimum_run_time` | Min run time for assets | Not set | CUSTOM |
| `required_response_time` | Response time for utilisation | Not set | CUSTOM |
| `dispatch_estimate` | Estimated dispatch events | Not set | CUSTOM |
| `dispatch_duration` | Estimated dispatch duration | Not set | CUSTOM |

### Configuration Modes

| Mode | Description |
|------|-------------|
| `REQUIRED_ONLY` | Only voltage requirements are included |
| `STANDARD` | Commonly used optional fields are included |
| `CUSTOM` | User-specified fields from available options |

## Advanced Configuration

### Parquet Processing

For parquet processing, additional command-line parameters are available:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--parquet` | Path to parquet file | N/A |
| `--filter` | Filter network groups (comma-separated) | All groups |
| `--workers` | Number of parallel workers | 4 |
| `--skip-existing` | Skip groups with existing results | False |

Example:
```bash
python firm_capacity_with_competitions.py --parquet data/raw/substations.parquet --filter substation1,substation2 --workers 2
```

### Column Mappings

When processing parquet files, the system uses column mappings to accommodate different naming conventions:

```python
COLUMN_MAPPINGS = {
    'group_name': 'Network Group Name',
    'timestamp': 'Timestamp',
    'network_group': 'Network Group Name',
    'demand_mw': 'Demand (MW)',
    'underlying_demand_mw': 'Demand (MW)',
}
```

These mappings allow the system to work with different column naming conventions in parquet files.