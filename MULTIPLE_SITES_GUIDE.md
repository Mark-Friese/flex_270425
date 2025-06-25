# Processing Multiple Sites with Known Firm Capacities

This guide shows you how to efficiently process 100+ sites with pre-calculated firm capacities. Your system has excellent built-in infrastructure for this!

## Quick Summary - Best Approaches for 100 Sites

### 1. **Parquet Method (Recommended for 100+ sites)**
- Store all demand data in a single parquet file
- Use parallel processing with `--workers 8` or more
- Filter specific sites with `--filter`
- Skip existing results with `--skip-existing`

### 2. **Batch Processing Script**  
- Use `batch_process_with_firm_capacities.py` for custom processing
- Parallel processing with progress tracking
- Error handling for individual sites

### 3. **Firm Capacities File**
- Use `--firm-capacities-file` with the main script
- CSV file with site names and firm capacities
- Automatic mapping to sites

## Method 1: Parquet Processing (Recommended)

### Setup Your Data

1. **Create a parquet file with all sites:**
```python
import pandas as pd

# Load all your CSV files
dfs = []
for site in ['Site1', 'Site2', ..., 'Site100']:
    df = pd.read_csv(f'data/{site}.csv')
    df['Network Group Name'] = site
    dfs.append(df)

# Combine into single parquet
combined_df = pd.concat(dfs, ignore_index=True)
combined_df.to_parquet('data/all_sites.parquet')
```

2. **Process all sites with known firm capacity:**
```bash
# Process all 100 sites in parallel with a single firm capacity
python firm_capacity_with_competitions.py \
    --parquet data/all_sites.parquet \
    --firm-capacity 25.5 \
    --workers 8 \
    --competitions \
    --skip-existing
```

3. **Process specific subsets:**
```bash
# Process only high-priority sites
python firm_capacity_with_competitions.py \
    --parquet data/all_sites.parquet \
    --filter "Site1,Site2,Site5,Site10" \
    --firm-capacity 30.0 \
    --workers 4 \
    --competitions
```

### Performance Optimization

For 100 sites, use these parameters:
- `--workers 8` (or number of CPU cores)
- `--skip-existing` to avoid reprocessing
- Filter to process in batches if needed

Expected processing time: **~2-5 minutes** for 100 sites with 8 workers.

## Method 2: Site-Specific Firm Capacities File

### 1. Create Firm Capacities CSV

```csv
Site,Firm_Capacity_MW
Site001,25.5
Site002,30.2
Site003,22.8
Site004,35.1
...
Site100,28.7
```

### 2. Process with Individual Capacities

```bash
# Each site uses its specific firm capacity
python firm_capacity_with_competitions.py \
    --config config.yaml \
    --firm-capacities-file firm_capacities.csv \
    --competitions \
    --workers 8
```

This will:
- Read each site's specific firm capacity
- Process all substations in your config
- Use parallel processing
- Generate service windows based on individual capacities

## Method 3: Custom Batch Processing Script

Use the new `batch_process_with_firm_capacities.py` script:

```bash
python batch_process_with_firm_capacities.py \
    --firm-capacities firm_capacities.csv \
    --config config.yaml \
    --workers 8 \
    --competitions \
    --skip-existing
```

### Features:
- **Progress tracking** with real-time updates
- **Error handling** for individual sites  
- **Detailed summary** with timing statistics
- **Resumable processing** with skip-existing
- **Flexible filtering** for site subsets

Example output:
```
Processing 100 sites with 8 workers
✅ Site001: 25.5 MW - Success
✅ Site002: 30.2 MW - Success
❌ Site003: 22.8 MW - Failed: File not found
Progress: 50/100 sites processed
...

🎯 Batch Processing Complete!
📁 Results saved to: output/
⏱️  Total time: 180.5 seconds
⚡ Average per site: 1.8 seconds
✅ Successful: 97
❌ Failed: 3
📊 Firm capacity range: 18.2 - 45.7 MW
```

## Method 4: Configuration File Approach

### Large Config File

For 100 sites, you can also use a large configuration file:

```yaml
substations:
  - name: "Site001"
    demand_file: "Site001.csv"
  - name: "Site002"
    demand_file: "Site002.csv"
  # ... repeat for all 100 sites
```

Then use:
```bash
python firm_capacity_with_competitions.py \
    --config config_100_sites.yaml \
    --firm-capacity 25.5 \
    --competitions
```

## Data Organization Strategies

### Option A: Individual CSV Files
```
data/
├── Site001.csv
├── Site002.csv
├── ...
└── Site100.csv
```

### Option B: Single Parquet File (Recommended)
```
data/
└── all_sites.parquet  # Contains all sites with 'Network Group Name' column
```

### Option C: Multiple Parquet Files
```
data/
├── sites_001_025.parquet
├── sites_026_050.parquet
├── sites_051_075.parquet
└── sites_076_100.parquet
```

## Performance Optimization Tips

### 1. Parallel Processing
- Use `--workers 8` (or your CPU core count)
- Higher worker counts for I/O-bound operations
- Lower for CPU-intensive calculations

### 2. Memory Management  
- Use parquet format for large datasets
- Process in batches if memory is limited
- Enable `--skip-existing` for resumable processing

### 3. Incremental Processing
```bash
# Process first 25 sites
python batch_process_with_firm_capacities.py \
    --firm-capacities firm_capacities.csv \
    --filter "Site001,Site002,...,Site025" \
    --workers 8

# Process next 25 (with skip-existing)
python batch_process_with_firm_capacities.py \
    --firm-capacities firm_capacities.csv \
    --filter "Site026,Site027,...,Site050" \
    --workers 8 \
    --skip-existing
```

### 4. Error Recovery
```bash
# Find failed sites from summary
grep "error" output/batch_processing_summary.csv

# Reprocess just the failed ones
python batch_process_with_firm_capacities.py \
    --firm-capacities firm_capacities.csv \
    --filter "Site003,Site015,Site042" \
    --workers 4
```

## Output Structure for 100 Sites

```
output/
├── Site001/
│   ├── competitions.json
│   ├── service_window_mwh.csv
│   ├── firm_capacity_results.csv
│   └── metadata.json
├── Site002/
│   └── ... (same structure)
├── ...
├── Site100/
│   └── ... (same structure)
├── batch_processing_summary.csv  # Overall summary
├── batch_processing_summary.json # Detailed results
└── parquet_summary.csv          # If using parquet
```

## Monitoring and Debugging

### 1. Check Progress
```bash
# Count completed sites
ls output/*/firm_capacity_results.csv | wc -l

# Check for errors
grep -l "error\|Error" output/*/metadata.json
```

### 2. Resource Usage
```bash
# Monitor during processing
top -p $(pgrep -f "firm_capacity_with_competitions")
htop
```

### 3. Log Files
```bash
# Save processing logs
python firm_capacity_with_competitions.py \
    --parquet data/all_sites.parquet \
    --firm-capacity 25.5 \
    --workers 8 \
    --competitions 2>&1 | tee processing.log
```

## Example Workflows

### Workflow 1: Quick Test with 5 Sites
```bash
# Test with a small subset first
python firm_capacity_with_competitions.py \
    --parquet data/all_sites.parquet \
    --filter "Site001,Site002,Site003,Site004,Site005" \
    --firm-capacity 25.0 \
    --workers 2 \
    --competitions
```

### Workflow 2: Full Production Run
```bash
# Process all 100 sites
python firm_capacity_with_competitions.py \
    --parquet data/all_sites.parquet \
    --firm-capacities-file firm_capacities.csv \
    --workers 8 \
    --competitions \
    --skip-existing \
    --year 2025
```

### Workflow 3: Error Recovery
```bash
# Check what failed
python -c "
import pandas as pd
df = pd.read_csv('output/parquet_summary.csv')
failed = df[df['Status'] == 'error']['Network Group']
print('Failed sites:', ', '.join(failed))
"

# Reprocess failed sites
python firm_capacity_with_competitions.py \
    --parquet data/all_sites.parquet \
    --filter "Site003,Site027,Site089" \
    --firm-capacities-file firm_capacities.csv \
    --workers 4 \
    --competitions
```

## Scaling to Even More Sites

For **1000+ sites**:

1. **Use Dask**: Install `pip install "dask[complete]"` for larger-than-memory processing
2. **Cloud Processing**: Consider cloud instances with more cores
3. **Chunked Processing**: Process in batches of 100-200 sites
4. **Database Storage**: Store results in a database instead of individual files

## Summary

**For 100 sites, I recommend:**

1. **Parquet method** with `--workers 8` for speed
2. **Firm capacities file** for individual site values
3. **Skip existing** for resumable processing  
4. **Batch scripts** for custom workflows

Expected processing time: **2-5 minutes** for 100 sites with proper parallelization.

Your system is already well-designed for this scale! 🚀 