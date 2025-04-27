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

    # load
    df = pd.read_csv(demand_path, parse_dates=["Timestamp"])
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
    for sub in cfg["substations"]:
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