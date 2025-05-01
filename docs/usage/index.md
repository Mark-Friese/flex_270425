# Getting Started with the Flexibility Analysis System

This guide will help you get up and running with the Flexibility Analysis System, covering basic usage and common workflows.

## Overview

The Flexibility Analysis System provides tools for analyzing power network demand data and generating flexibility service competitions. The system consists of:

1. **Command-line tools** for analyzing data and generating competitions
2. **Desktop application** for interactive visualization and analysis
3. **Python libraries** for advanced customization and integration

## Quick Start

The fastest way to get started is to run a basic analysis using the command-line interface.

### 1. Configure the System

Create or modify a `config.yaml` file with your settings:

```yaml
input:
  demand_base_dir: "./data/samples/"
  in_substation_folder: false

output:
  base_dir: "./output"

firm_capacity:
  target_mwh: 300.0
  tolerance: 0.01

substations:
  - name: substation1
    demand_file: "substation1.csv"
```

### 2. Run a Basic Analysis

```bash
python firm_capacity_analysis/src/main.py
```

### 3. Generate Competitions

```bash
python firm_capacity_analysis/firm_capacity_with_competitions.py --competitions
```

### 4. View the Results

Check the output directory for results:
- `E_curve_plain.png` and `E_curve_peak.png` for energy curve plots
- `firm_capacity_results.csv` for tabular results
- `metadata.json` for detailed metadata
- `competitions.json` for generated competitions (if enabled)

## Common Workflows

### Analyzing a Single Substation

```bash
python firm_capacity_analysis/firm_capacity_with_competitions.py --competitions --filter Substation1
```

### Processing Large Datasets

```bash
python firm_capacity_analysis/firm_capacity_with_competitions.py \
  --competitions \
  --parquet data/raw/substations.parquet \
  --workers 4
```

### Using Site-Specific Targets

```bash
python firm_capacity_analysis/firm_capacity_with_competitions.py \
  --competitions \
  --targets data/samples/site_targets.csv
```

### Running the Desktop Application

```bash
python firm_capacity_analysis/app.py
```

## Next Steps

- Learn about [Command Line Options](command-line.md)
- Understand [Configuration Options](configuration.md)
- Explore the [Desktop Application](desktop-app.md)
- Process [Parquet Files](parquet-processing.md)
- Understand the [Mathematical Models](../technical/mathematical-models.md)