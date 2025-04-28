"""
firm_capacity_with_competitions.py - Main script for firm capacity analysis with competition generation

This script extends the firm capacity analysis to generate flexibility competitions
according to the flexibility competition schema, using the same logic as energy_peak_based
for service window identification.
"""

import pandas as pd
import json
import numpy as np
from pathlib import Path
import argparse
import logging
import sys
import os
from datetime import datetime
from typing import List, Dict, Optional, Union, Tuple

# Import original firm capacity modules
from src.utils import load_config, ensure_dir
from src.calculations import (
    energy_above_capacity,
    energy_peak_based,
    invert_capacity,
)
from src.plotting import plot_E_curve

# Import competition modules (new additions)
from competition_builder import (
    create_competitions_from_df,
    save_competitions_to_json,
    validate_competitions_with_schema
)
from competition_dates import update_dates_in_dataframe
from competition_config import ConfigMode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def process_substation_with_competitions(
    cfg: dict, 
    sub: dict, 
    generate_competitions: bool = True,
    target_year: Optional[int] = None,
    schema_path: Optional[str] = None
):
    """
    Process a substation with firm capacity analysis and optionally generate competitions.
    
    Args:
        cfg: Configuration dictionary
        sub: Substation configuration dictionary
        generate_competitions: Whether to generate competitions
        target_year: Optional year to use for dates in competition generation
        schema_path: Optional path to competition schema for validation
    """
    name = sub["name"]
    out_base = Path(cfg["output"]["base_dir"]) / name
    ensure_dir(out_base)

    # Locate demand CSV
    if cfg["input"]["in_substation_folder"]:
        demand_path = out_base / sub["demand_file"]
    else:
        demand_path = Path(cfg["input"]["demand_base_dir"]) / f"{name}.csv"

    # Load demand data
    df = pd.read_csv(demand_path, parse_dates=["Timestamp"])
    df.sort_values("Timestamp", inplace=True)
    
    # Add substation name column if not present
    if "Substation" not in df.columns:
        df["Substation"] = name
    
    # Determine time step from data
    if len(df) > 1:
        time_diff = (df["Timestamp"].iloc[1] - df["Timestamp"].iloc[0]).total_seconds() / 3600  # in hours
        delta_t = time_diff
    else:
        # Default to half-hourly if can't determine
        delta_t = 0.5
    
    # Update dates if target_year is specified
    if target_year is not None:
        df = update_dates_in_dataframe(df, target_year=target_year)
    
    # Original firm capacity calculations
    demand = df["Demand (MW)"].values
    T = cfg["firm_capacity"]["target_mwh"]
    tol_frac = cfg["firm_capacity"]["tolerance"]
    
    try:
        tol_C = tol_frac * float(demand.max()) # Use float() just in case
    except ValueError:
        logger.warning(f"Warning: Could not determine max demand for {name}, using default tolerance.")
        tol_C = 1e-3 # Default absolute tolerance if max fails

    # Calculate firm capacity using different methods
    C_plain = invert_capacity(energy_above_capacity, demand, T, tol=tol_C)
    C_peak = invert_capacity(energy_peak_based, demand, T, tol=tol_C)

    # Generate plots
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

    # Calculate the actual energy for verification
    energy_peak = energy_peak_based(demand, C_peak)

    # Summary stats
    stats = {
        "substation": name,
        "C_plain_MW": C_plain,
        "C_peak_MW": C_peak,
        "mean_demand_MW": float(demand.mean()),
        "max_demand_MW": float(demand.max()),
        "total_energy_MWh": float((demand * delta_t).sum()),
        "energy_above_capacity_MWh": float(energy_peak)
    }
    
    # Write results
    pd.DataFrame([stats]).to_csv(out_base/"firm_capacity_results.csv", index=False)
    
    # Write metadata
    with open(out_base/"metadata.json","w") as f:
        json.dump(stats, f, indent=2)
    
    # Generate competitions if requested
    if generate_competitions:
        logger.info(f"Generating competitions for {name} with firm capacity {C_peak:.2f} MW")
        
        # Get competition settings from config
        comp_cfg = cfg.get("competitions", {})
        procurement_window_size_minutes = comp_cfg.get("procurement_window_size_minutes", 30)
        daily_service_periods = comp_cfg.get("daily_service_periods", False)
        financial_year = comp_cfg.get("financial_year", None)
        
        # Generate competitions using C_peak as the firm capacity
        competitions = create_competitions_from_df(
            df,
            C_peak,  # Use the peak-based firm capacity
            schema_path=schema_path,
            procurement_window_size_minutes=procurement_window_size_minutes,
            daily_service_periods=daily_service_periods,
            financial_year=financial_year,
            delta_t=delta_t  # Pass the time step determined from data
        )
        
        if competitions:
            # Save competitions to JSON
            competitions_path = out_base / "competitions.json"
            save_competitions_to_json(competitions, str(competitions_path))
            logger.info(f"Saved {len(competitions)} competitions to {competitions_path}")
            
            # Validate competitions if schema path is provided
            if schema_path:
                validation_errors = validate_competitions_with_schema(competitions, schema_path)
                
                if validation_errors:
                    # Save validation errors to JSON
                    error_path = out_base / "validation_errors.json"
                    with open(error_path, "w") as f:
                        json.dump(validation_errors, f, indent=2)
                    logger.warning(f"Found {len(validation_errors)} validation errors. See {error_path} for details.")
                else:
                    logger.info("All competitions validated successfully against schema.")
        else:
            logger.warning(f"No competitions generated for {name}")
    
    return stats

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Firm capacity analysis with competition generation")
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to config file')
    parser.add_argument('--competitions', action='store_true', help='Generate competitions')
    parser.add_argument('--schema', type=str, help='Path to competition schema for validation')
    parser.add_argument('--year', type=int, help='Target year for competition dates')
    
    args = parser.parse_args()
    
    # Load configuration
    config_path = Path(args.config)
    if not config_path.is_absolute():
        # Use the script's directory if the path is relative
        config_path = Path(__file__).resolve().parent / args.config
    
    cfg = load_config(config_path)
    
    # Add default competitions section if not present
    if "competitions" not in cfg:
        cfg["competitions"] = {
            "procurement_window_size_minutes": 30,
            "daily_service_periods": False,
            "financial_year": None
        }
    
    # Process each substation
    results = []
    for sub in cfg["substations"]:
        try:
            result = process_substation_with_competitions(
                cfg, 
                sub, 
                generate_competitions=args.competitions,
                target_year=args.year,
                schema_path=args.schema
            )
            results.append(result)
            logger.info(f"Successfully processed {sub['name']}")
        except FileNotFoundError:
            if cfg["input"]["in_substation_folder"]:
                demand_path = Path(cfg["output"]["base_dir"]) / sub["name"] / sub["demand_file"]
            else:
                demand_path = Path(cfg["input"]["demand_base_dir"]) / f"{sub['name']}.csv"
            logger.error(f"Error: Demand file not found for {sub['name']}. Expected at: {demand_path}")
            logger.error(f"Please check config.yaml and ensure data files exist.")
        except Exception as e:
            logger.error(f"Error processing {sub['name']}: {e}", exc_info=True)
    
    # Combine results into summary
    if results:
        summary_df = pd.DataFrame(results)
        summary_path = Path(cfg["output"]["base_dir"]) / "summary.csv"
        summary_df.to_csv(summary_path, index=False)
        logger.info(f"Summary saved to {summary_path}")

if __name__ == "__main__":
    main()
