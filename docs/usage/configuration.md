# Configuration Guide

This guide explains how to configure the Flexibility Analysis System through its YAML configuration files.

## Configuration File Structure

The system uses YAML configuration files with several key sections:

```yaml
input:
  # Input data configuration
  demand_base_dir: "./data/samples/"
  in_substation_folder: false
  metadata_file: "./data/metadata.csv"

output:
  # Output directory configuration
  base_dir: "./output"

firm_capacity:
  # Firm capacity calculation parameters
  target_mwh: 300.0     # Target energy threshold in MWh
  tolerance: 0.01       # Tolerance for bisection search

competitions:
  # Competition generation parameters
  procurement_window_size_minutes: 30
  disaggregate_days: true
  daily_service_periods: true
  financial_year: "2025/26"

substations:
  # List of substations to process
  - name: "substation1" 
    demand_file: "substation1.csv"
  - name: "substation2"
    demand_file: "substation2.csv"
```

## Key Configuration Sections

### Input Configuration

```yaml
input:
  demand_base_dir: "./data/samples/"    # Base directory for demand data
  in_substation_folder: false           # Whether data is in substation-specific folders
  metadata_file: "./data/metadata.csv"  # Optional metadata file
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `demand_base_dir` | Directory containing demand data files | `"./data/samples/"` |
| `in_substation_folder` | If true, looks for data in substation-named subfolders | `false` |
| `metadata_file` | Optional metadata file with additional substation information | `null` |

#### Data Location Logic

When `in_substation_folder` is `false` (default):
- The system looks for files at `{demand_base_dir}/{substation_name}.csv`
- Example: `./data/samples/substation1.csv`

When `in_substation_folder` is `true`:
- The system looks for files at `{output_base_dir}/{substation_name}/{demand_file}`
- Example: `./output/substation1/demand.csv`

### Output Configuration

```yaml
output:
  base_dir: "./output"  # Base directory for output files
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `base_dir` | Directory where output files will be created | `"./output"` |

Output is organized into substation-specific folders:
```
output/
└── {substation_name}/
    ├── E_curve_plain.png         # Plot for plain E(C) curve
    ├── E_curve_peak.png          # Plot for peak-based E(C) curve
    ├── firm_capacity_results.csv # Tabular results
    ├── metadata.json             # Metadata in JSON format
    ├── competitions.json         # Generated competitions (if enabled)
    └── service_window_mwh.csv    # Service window MWh data (if generated)
```

### Firm Capacity Configuration

```yaml
firm_capacity:
  target_mwh: 300.0  # Target energy threshold in MWh
  tolerance: 0.01    # Tolerance for bisection search
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `target_mwh` | Target energy threshold in MWh for firm capacity inversion | `300.0` |
| `tolerance` | Tolerance for bisection search (relative to maximum demand) | `0.01` |

#### Target MWh Impact

The `target_mwh` parameter significantly impacts the calculated firm capacity:
- Higher values result in lower firm capacity
- Lower values result in higher firm capacity

For fine-tuning, you can use site-specific targets via a CSV file:
```bash
python firm_capacity_with_competitions.py --targets data/samples/site_targets.csv
```

### Competition Configuration

```yaml
competitions:
  procurement_window_size_minutes: 30  # Size of procurement windows
  disaggregate_days: true              # Whether to disaggregate days
  daily_service_periods: true          # Group by day instead of month
  financial_year: "2025/26"            # Financial year for dates
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `procurement_window_size_minutes` | Size of individual service windows in minutes | `30` |
| `disaggregate_days` | Whether to create separate windows for each day of week | `false` |
| `daily_service_periods` | Group windows by day instead of by month | `false` |
| `financial_year` | Financial year for competition dates (format: "YYYY/YY") | `null` |

#### Window Duration Impact

The `procurement_window_size_minutes` parameter affects the granularity of service windows:
- Smaller values (e.g., 30 minutes) create more, shorter windows
- Larger values (e.g., 120 minutes) create fewer, longer windows

#### Service Period Grouping

When `daily_service_periods` is `false`:
- Service windows are grouped into monthly periods
- Each month with overloads gets one service period
- Example period name: "January"

When `daily_service_periods` is `true`:
- Service windows are grouped by specific days
- Each day with overloads gets a separate service period
- Example period name: "January 15 (Monday)"

### Substations Configuration

```yaml
substations:
  - name: "substation1"           # Substation name
    demand_file: "substation1.csv"  # Demand data file
  - name: "substation2"
    demand_file: "substation2.csv"
```

| Parameter | Description | Required |
|-----------|-------------|----------|
| `name` | Substation name (used for folder and competition naming) | Yes |
| `demand_file` | Name of the demand data file | Yes if `in_substation_folder` is true |

## Using Multiple Configuration Files

You can maintain multiple configuration files for different scenarios:

```bash
# Standard configuration
python firm_capacity_with_competitions.py --config config.yaml

# Configuration with competitions
python firm_capacity_with_competitions.py --config config_with_competitions.yaml --competitions
```

## Configuration File Validation

The system will validate your configuration file at startup and report any issues:

- Missing required parameters
- Invalid parameter types
- Inconsistent configuration combinations

Example validation error:
```
Error in configuration: demand_base_dir not found in input section
```

## Dynamic Configuration via Command Line

Some configuration options can be overridden via command-line parameters:

```bash
python firm_capacity_with_competitions.py --year 2025 --targets data/samples/site_targets.csv
```

These parameters override their corresponding configuration file values.

## Configuration Best Practices

1. **Use relative paths** for portability:
   ```yaml
   input:
     demand_base_dir: "./data/samples/"
   ```

2. **Enable daily service periods** for more detailed competition generation:
   ```yaml
   competitions:
     daily_service_periods: true
   ```

3. **Set appropriate target values** based on your network requirements:
   ```yaml
   firm_capacity:
     target_mwh: 300.0
   ```

4. **Use site-specific targets** for fine-grained control:
   ```csv
   site_name,target_mwh
   substation1,150
   substation2,250
   ```

5. **Create scenario-specific configurations** for different analyses:
   - `config_base.yaml`: Basic firm capacity analysis
   - `config_competitions.yaml`: Full competition generation
   - `config_scenario_2030.yaml`: Future scenario analysis