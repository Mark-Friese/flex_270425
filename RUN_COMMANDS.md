# Cheatsheet: Running Firm Capacity Analysis

This script calculates firm capacity metrics for electrical substations based on demand data.

## Configuration

All configuration is managed in the `firm_capacity_analysis/config.yaml` file. Before running the script, ensure this file contains the correct settings for:

-   Input data locations (`input.demand_base_dir` or `input.in_substation_folder`)
-   Output directory (`output.base_dir`)
-   Firm capacity parameters (`firm_capacity.target_mwh`, `firm_capacity.tolerance`)
-   Substation details (list under `substations`, including `name` and potentially `demand_file` if `in_substation_folder` is true)

## Running the Script

To run the analysis, navigate to the project's root directory (`flex_270425`) in your terminal and execute the `main.py` script using Python.

**Command:**

```bash
# Make sure you are in the flex_270425 directory
# Activate your Python environment if necessary (e.g., venv)
python firm_capacity_analysis/src/main.py
```

The script will:

1.  Read the configuration from `firm_capacity_analysis/config.yaml`.
2.  Process each substation defined in the configuration.
3.  Load the corresponding demand data CSV file.
4.  Perform calculations (`energy_above_capacity`, `energy_peak_based`, `invert_capacity`).
5.  Generate output plots (`E_curve_plain.png`, `E_curve_peak.png`) and results (`firm_capacity_results.csv`, `metadata.json`) in the specified output directory for each substation.
6.  Print status messages or errors to the console.

**Example Output Location:**

If `output.base_dir` is set to `output` in `config.yaml` and a substation name is `SubstationA`, the results for that substation will be saved in:

`firm_capacity_analysis/output/SubstationA/`

--- 