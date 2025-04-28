# src/main.py
import pandas as pd
import json
from pathlib import Path
from utils import load_config, ensure_dir
from calculations import (
    energy_above_capacity,
    energy_peak_based,
    invert_capacity,
)
from plotting import plot_E_curve

def process_substation(cfg: dict, sub: dict):
    name      = sub["name"]
    out_base  = Path(cfg["output"]["base_dir"]) / name
    ensure_dir(out_base)

    # locate demand CSV
    if cfg["input"]["in_substation_folder"]:
        demand_path = out_base / sub["demand_file"]
    else:
        demand_path = Path(cfg["input"]["demand_base_dir"]) / f"{name}.csv"

    # load (read without parsing dates initially)
    try:
        df = pd.read_csv(demand_path)
    except FileNotFoundError:
        # This exception should ideally be caught in main, but handle here too for safety
        print(f"Error: Demand file not found for {name}. Expected at: {demand_path}")
        raise # Re-raise to be caught and logged in main()
    except Exception as e:
        print(f"Error reading CSV file {demand_path} for {name}: {e}")
        raise # Re-raise

    # Explicitly parse timestamps, coercing errors
    if "Timestamp" not in df.columns:
        print(f"Error: 'Timestamp' column not found in {demand_path} for {name}.")
        # Decide how to handle: raise error, return, etc.
        raise ValueError(f"'Timestamp' column missing in {demand_path}")

    original_rows = len(df)
    # Use explicit ISO8601 format parsing
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors='coerce', format='iso8601')

    # Check how many rows were affected by coercion
    invalid_timestamps = df["Timestamp"].isna().sum()
    if invalid_timestamps > 0:
        print(f"Warning: Found {invalid_timestamps} invalid timestamps in {demand_path} for {name}. They will be treated as missing data (NaT).")
        # Option: Remove rows with invalid dates
        df.dropna(subset=['Timestamp'], inplace=True)
        print(f"Removed {invalid_timestamps} rows with invalid timestamps for {name}. {len(df)} rows remaining.")

    # Check if dataframe is empty after removing NaTs
    if df.empty:
        print(f"Error: No valid data rows remain for {name} after handling timestamps in {demand_path}.")
        # Decide how to handle: return, raise error, etc.
        # For now, let's raise an error to stop processing this substation
        raise ValueError(f"No valid timestamp data for {name} in {demand_path}")

    df.sort_values("Timestamp", inplace=True)
    demand = df["Demand (MW)"].values

    # compute
    T       = cfg["firm_capacity"]["target_mwh"]
    tol_frac= cfg["firm_capacity"]["tolerance"]
    # Note: The original guide didn't define tol_C calculation relative to demand.max()
    # It's used in invert_capacity call. Let's calculate it here.
    # tol_C   = tol_frac * demand.max() # This might cause NameError if demand is empty or max is weird.
                                      # Using the tolerance fraction directly as relative tolerance in bisection might be safer.
                                      # However, the original code passes tol=tol_C, implying absolute tolerance.
                                      # Let's stick to the original guide's apparent intent, assuming demand.max() is valid.
    try:
      tol_C = tol_frac * float(demand.max()) # Use float() just in case
    except ValueError:
      print(f"Warning: Could not determine max demand for {name}, using default tolerance.")
      tol_C = 1e-3 # Default absolute tolerance if max fails

    C_plain = invert_capacity(energy_above_capacity, demand, T, tol=tol_C)
    C_peak  = invert_capacity(energy_peak_based,  demand, T, tol=tol_C)

    # plots
    plot_E_curve(
        demand, energy_above_capacity,
        C_plain, T,
        out_base/"E_curve_plain.png",
        f"{name}: Plain E(C)"
    )
    plot_E_curve(
        demand, energy_peak_based,
        C_peak, T,
        out_base/"E_curve_peak.png",
        f"{name}: Peak‐based E(C)"
    )

    # summary stats
    stats = {
        "substation": name,
        "C_plain_MW": C_plain,
        "C_peak_MW": C_peak,
        "mean_demand_MW": float(demand.mean()),
        "max_demand_MW": float(demand.max()),
        "total_energy_MWh": float((demand*0.5).sum())
    }
    # write results
    pd.DataFrame([stats]).to_csv(out_base/"firm_capacity_results.csv", index=False)
    # write metadata
    with open(out_base/"metadata.json","w") as f:
        json.dump(stats, f, indent=2)

def main():
    # Correct path calculation relative to main.py
    config_path = Path(__file__).resolve().parent.parent / "config.yaml"
    cfg = load_config(config_path)
    # Process only the first two substations for testing
    for sub in cfg["substations"][:2]:
        # Calculate demand_path here to make it available in the except block
        name = sub["name"] # Need name for path calculation
        if cfg["input"]["in_substation_folder"]:
            # This case needs careful handling if out_base is defined inside process_substation
            # For simplicity, let's assume in_substation_folder=false for now based on config.yaml
            # If true, this logic needs adjustment, potentially moving out_base calculation here too.
             # Assuming the base path logic needs to be consistent
            out_base = Path(cfg["output"]["base_dir"]) / name # Define out_base here too if needed
            demand_path = out_base / sub["demand_file"]
        else:
            demand_path = Path(cfg["input"]["demand_base_dir"]) / f"{name}.csv"

        try:
            process_substation(cfg, sub)
            print(f"Successfully processed {sub['name']}")
        except FileNotFoundError:
             print(f"Error: Demand file not found for {sub['name']}. Expected at: {demand_path}")
             print(f"Please check config.yaml and ensure data files exist.")
        except Exception as e:
            print(f"Error processing {sub['name']}: {e}")

if __name__ == "__main__":
    main() 