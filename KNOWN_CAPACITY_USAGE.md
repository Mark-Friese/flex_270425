# Using Known Firm Capacities (No Target MWh Required)

When you already have firm capacity values, you **don't need** to specify a target MWh in your configuration! The script now handles this automatically.

## The Issue You Found

✅ **You're correct!** When using known firm capacities, requiring a target MWh doesn't make logical sense because:

- **Target MWh** is used to *calculate* firm capacity through iteration
- **Known firm capacity** bypasses this calculation entirely
- The system was still expecting the config field even when not using it

## ✅ Fixed!

The script now automatically handles this by:

1. **Auto-creating config defaults** when using `--firm-capacity` or `--firm-capacities-file`
2. **Not requiring** `firm_capacity.target_mwh` in your config
3. **Providing minimal config** examples for known capacity workflows

## Quick Usage Examples

### 1. Single Firm Capacity for All Sites

```bash
# Use minimal config - no target_mwh needed!
python firm_capacity_with_competitions.py \
    --config config_minimal_for_known_capacity.yaml \
    --firm-capacity 25.5 \
    --competitions
```

### 2. Individual Firm Capacities per Site

```bash
# Each site gets its own firm capacity
python firm_capacity_with_competitions.py \
    --config config_minimal_for_known_capacity.yaml \
    --firm-capacities-file firm_capacities.csv \
    --competitions
```

### 3. Parquet Processing with Known Capacities

```bash
# Process 100+ sites with a single firm capacity
python firm_capacity_with_competitions.py \
    --parquet data/all_sites.parquet \
    --firm-capacity 25.5 \
    --workers 8 \
    --competitions
```

## Minimal Configuration File

Use `config_minimal_for_known_capacity.yaml`:

```yaml
# No firm_capacity section needed!
input:
  demand_base_dir: "data"
  in_substation_folder: false

output:
  base_dir: "output"

substations:
  - name: "Site1"
    demand_file: "Site1.csv"
  - name: "Site2"
    demand_file: "Site2.csv"

competitions:
  procurement_window_size_minutes: 30
  daily_service_periods: false
```

## What's Different

### ❌ Old Way (Required target_mwh even when not needed)
```yaml
firm_capacity:
  target_mwh: 100  # This was required even with known capacities!
  tolerance: 0.01
```

### ✅ New Way (Automatic when using known capacities)
```bash
# Just provide the firm capacity directly
python firm_capacity_with_competitions.py \
    --config config_minimal.yaml \
    --firm-capacity 25.5
```

The script automatically adds the `firm_capacity` config section internally when needed, so you don't have to!

## Backwards Compatibility

✅ **Your existing configs still work!** 

- If you have `firm_capacity.target_mwh` in your config → still works
- If you don't have it but use `--firm-capacity` → automatically handled
- Mix of calculated and known capacities → works perfectly

## Command Examples

```bash
# Minimal - single capacity
python firm_capacity_with_competitions.py \
    --config config_minimal_for_known_capacity.yaml \
    --firm-capacity 25.5

# Individual capacities per site  
python firm_capacity_with_competitions.py \
    --config config_minimal_for_known_capacity.yaml \
    --firm-capacities-file capacities.csv

# Parquet with 100 sites
python firm_capacity_with_competitions.py \
    --parquet all_sites.parquet \
    --firm-capacity 25.5 \
    --workers 8

# Mix: some sites calculated, some known
python firm_capacity_with_competitions.py \
    --config full_config.yaml \
    --firm-capacities-file some_known_capacities.csv
```

## Files You Need

### For Known Capacities:
1. **Demand data**: `Site1.csv`, `Site2.csv`, etc.
2. **Minimal config**: `config_minimal_for_known_capacity.yaml`  
3. **Firm capacities** (one of):
   - Single value: `--firm-capacity 25.5`
   - Per-site file: `firm_capacities.csv`

### You DON'T Need:
- ❌ `target_mwh` in config  
- ❌ `tolerance` values
- ❌ Complex configuration

## Summary

**Problem**: Script expected target MWh even with known firm capacities
**Solution**: Automatic config handling when using `--firm-capacity` or `--firm-capacities-file`
**Result**: Clean, logical workflow that doesn't require irrelevant config fields

Your observation was spot on - this is much more logical now! 🎯 