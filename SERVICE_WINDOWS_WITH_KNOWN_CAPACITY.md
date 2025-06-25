# Generating Service Windows with Known Firm Capacity

This guide explains how to generate service windows and flexibility competitions when you already have a firm capacity value, without needing to calculate it first.

## Quick Answer

**Yes, you can absolutely create service windows when you already have the firm capacity!** 

The system is designed to work with pre-calculated firm capacity values. You just need to skip the capacity calculation step and provide your known value directly.

## How It Works

The service window generation process consists of these steps:

1. **Load demand data** (CSV with Timestamp and Demand columns)
2. **Use your firm capacity value** (instead of calculating it)
3. **Identify overload segments** where demand exceeds firm capacity
4. **Create service windows** from these segments
5. **Generate competitions** containing the service windows

## Methods to Use Known Firm Capacity

### Method 1: Command Line (Easiest)

Use the `--firm-capacity` argument with the main script:

```bash
python firm_capacity_with_competitions.py \
    --config config.yaml \
    --competitions \
    --firm-capacity 25.5
```

This will:
- Skip the firm capacity calculation
- Use 25.5 MW as the firm capacity
- Generate service windows for all demand above this threshold
- Create competitions with the service windows

### Method 2: Python Function (Programmatic)

Use the new `create_service_windows_with_known_capacity()` function:

```python
from firm_capacity_with_competitions import create_service_windows_with_known_capacity

# Your configuration
cfg = load_config("config.yaml")
sub = {"name": "MySubstation", "demand_file": "demand.csv"}
firm_capacity = 25.5  # Your known firm capacity in MW

# Generate service windows
result = create_service_windows_with_known_capacity(
    cfg=cfg,
    sub=sub,
    firm_capacity=firm_capacity,
    generate_competitions=True
)
```

### Method 3: Direct API (Most Flexible)

Use the competition builder directly:

```python
import pandas as pd
from competition_builder import create_competitions_from_df

# Load your demand data
df = pd.read_csv("demand.csv", parse_dates=["Timestamp"])
firm_capacity = 25.5  # Your known firm capacity

# Generate competitions directly
competitions = create_competitions_from_df(
    df=df,
    firm_capacity=firm_capacity,
    procurement_window_size_minutes=30,
    daily_service_periods=False
)
```

## Example Script

I've created `example_with_known_capacity.py` that demonstrates this:

```python
#!/usr/bin/env python3
from competition_builder import create_competitions_from_df, save_competitions_to_json
from firm_capacity_with_competitions import generate_service_window_mwh

def generate_service_windows_with_known_capacity(
    demand_file: str,
    firm_capacity: float,
    output_dir: str = "output"
):
    # Load demand data
    df = pd.read_csv(demand_file, parse_dates=["Timestamp"])
    
    # Generate competitions with known firm capacity
    competitions = create_competitions_from_df(
        df,
        firm_capacity,  # Use your known value
        procurement_window_size_minutes=30
    )
    
    # Save results
    save_competitions_to_json(competitions, f"{output_dir}/competitions.json")
    generate_service_window_mwh(competitions, f"{output_dir}/service_windows.csv")
    
    return competitions

# Usage
competitions = generate_service_windows_with_known_capacity(
    demand_file="my_demand_data.csv",
    firm_capacity=25.5  # MW
)
```

## What Gets Generated

When you provide a firm capacity, the system generates:

### 1. Service Windows
Time periods when demand exceeds your firm capacity:
- **When**: Specific days and times (e.g., "Monday 17:00-19:30")
- **Capacity Required**: How much reduction is needed (peak demand - firm capacity)
- **Energy (MWh)**: Total energy above the threshold
- **Duration**: How long the overload lasts

### 2. Service Periods
Groupings of service windows by month or day:
- **Monthly**: All windows in January, February, etc.
- **Daily**: Separate period for each day with overloads

### 3. Competitions
Complete flexibility competition structures including:
- Competition metadata (names, dates, references)
- Service periods with their service windows
- All required fields for flexibility procurement

### 4. Summary Data
CSV files with:
- Service window details (times, capacity, energy)
- MWh totals and statistics
- Validation against your firm capacity

## Data Requirements

Your demand data CSV must have:
- `Timestamp` column (datetime format)
- `Demand (MW)` column (numeric values)

Example:
```csv
Timestamp,Demand (MW)
2024-01-01 00:00:00,22.5
2024-01-01 00:30:00,23.1
2024-01-01 01:00:00,26.8
...
```

## Configuration Options

You can customize the service window generation:

```python
competitions = create_competitions_from_df(
    df=df,
    firm_capacity=25.5,
    procurement_window_size_minutes=30,  # Window granularity
    daily_service_periods=False,         # Group by month vs day
    financial_year="2025/26",           # Optional financial year
    delta_t=0.5                         # Time step (hours)
)
```

## Key Benefits

1. **No Iterative Calculation**: Skip the expensive firm capacity calculation
2. **Direct Control**: Use your exact capacity value
3. **Consistent Results**: Same service windows every time
4. **Fast Processing**: Much quicker than calculating capacity first
5. **Flexible Integration**: Works with existing tools and workflows

## Validation

The system validates that:
- Total energy in service windows matches the energy above your firm capacity
- Service windows only occur when demand exceeds the threshold
- All required competition fields are properly formatted
- Time periods are consistent and non-overlapping

## Example Output

With a firm capacity of 25.5 MW, you might get:

```
Service Windows Generated:
- Monday 17:00-19:30: 2.3 MW reduction, 5.75 MWh
- Tuesday 18:00-20:00: 1.8 MW reduction, 3.60 MWh  
- Friday 16:30-18:00: 3.1 MW reduction, 4.65 MWh

Total: 3 service windows, 13.4 MWh above capacity
```

## When to Use This

This approach is ideal when you:
- Already know the firm capacity from previous analysis
- Want to test different capacity scenarios quickly
- Need consistent service windows for planning
- Are integrating with other tools that provide firm capacity
- Want to skip the computational overhead of capacity calculation

The system is designed to be flexible - use whatever firm capacity value makes sense for your analysis! 