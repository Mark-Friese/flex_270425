# src/main.py
import pandas as pd
import json
from pathlib import Path
from utils import load_config, ensure_dir, load_site_specific_targets
from calculations import (
    energy_above_capacity,
    energy_peak_based,
    invert_capacity,
)
from plotting import plot_E_curve
from typing import Optional, Dict
import logging
import argparse

logger = logging.getLogger(__name__)

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

def process_substation_with_competitions(
    cfg: dict, 
    sub: dict, 
    generate_competitions: bool = True,
    target_year: Optional[int] = None,
    schema_path: Optional[str] = None,
    parquet_path: Optional[str] = None,
    parquet_df: Optional[pd.DataFrame] = None,
    site_targets: Optional[Dict[str, float]] = None
):
    """
    Process a substation with firm capacity analysis and optionally generate competitions.
    
    Args:
        cfg: Configuration dictionary
        sub: Substation configuration dictionary
        generate_competitions: Whether to generate competitions
        target_year: Optional year to use for dates in competition generation
        schema_path: Optional path to competition schema for validation
        parquet_path: Optional path to parquet file (for logging)
        parquet_df: Optional pre-filtered dataframe from parquet
        site_targets: Optional dictionary of site-specific MWh targets
    """
    name = sub["name"]
    out_base = Path(cfg["output"]["base_dir"]) / name
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

    # Use site-specific target if available, otherwise use default from config
    if site_targets and name in site_targets:
        T = site_targets[name]
        logger.info(f"Using site-specific target for {name}: {T} MWh")
    else:
        T = cfg["firm_capacity"]["target_mwh"]
        logger.info(f"Using default target from config for {name}: {T} MWh")
    
    tol_frac = cfg["firm_capacity"]["tolerance"]

    # compute
    tol_C = tol_frac * float(demand.max()) # Use float() just in case

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
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Firm capacity analysis with competition generation")
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to config file')
    parser.add_argument('--competitions', action='store_true', help='Generate competitions')
    parser.add_argument('--schema', type=str, help='Path to competition schema for validation')
    parser.add_argument('--year', type=int, help='Target year for competition dates')
    
    # Add targets file argument
    parser.add_argument('--targets', type=str, help='Path to CSV file with site-specific MWh targets')
    
    # Add parquet arguments
    parser.add_argument('--parquet', type=str, help='Path to parquet file with substation demand data')
    parser.add_argument('--filter', type=str, help='Filter network groups (comma-separated)')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers for parquet processing')
    parser.add_argument('--skip-existing', action='store_true', help='Skip network groups with existing results')
    
    args = parser.parse_args()
    
    # Load configuration
    config_path = Path(args.config)
    if not config_path.is_absolute():
        # Use the script's directory if the path is relative
        config_path = Path(__file__).resolve().parent / args.config
    
    cfg = load_config(config_path)
    
    # Load site-specific targets if provided
    site_targets = None
    if args.targets:
        targets_path = Path(args.targets)
        if not targets_path.is_absolute():
            targets_path = Path(__file__).resolve().parent / args.targets
        
        try:
            site_targets = load_site_specific_targets(targets_path)
            logger.info(f"Loaded {len(site_targets)} site-specific targets from {targets_path}")
        except Exception as e:
            logger.error(f"Error loading targets file: {e}")
            logger.warning("Will use default target from config instead")
    
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

    # For parquet processing:
    results = process_network_groups_in_parquet(
        args.parquet,
        cfg,
        process_substation_with_competitions,
        network_groups=filter_groups,
        max_workers=args.workers,
        skip_existing=args.skip_existing,
        generate_competitions=args.competitions,
        target_year=args.year,
        schema_path=args.schema,
        site_targets=site_targets  # Add this parameter
    )
    
    # For regular processing:
    result = process_substation_with_competitions(
        cfg, 
        sub, 
        generate_competitions=args.competitions,
        target_year=args.year,
        schema_path=args.schema,
        site_targets=site_targets  # Add this parameter
    )

if __name__ == "__main__":
    main() 