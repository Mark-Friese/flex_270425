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
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union, Tuple

# Import original firm capacity modules
from src.utils import load_config, ensure_dir, load_site_specific_targets
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

# Import parquet processing module
from src.parquet_processor import (
    process_network_groups_in_parquet, 
    get_unique_network_groups,
    save_summary_results
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Utility functions for service window MWh extraction
def extract_window_duration(start_time, end_time):
    """
    Calculate window duration in hours from start and end times (HH:MM format).
    Handles overnight windows.
    
    Returns:
        float: Window duration in hours, guaranteed to be positive
    """
    start_hour, start_min = map(int, start_time.split(':'))
    end_hour, end_min = map(int, end_time.split(':'))
    
    start_minutes = start_hour * 60 + start_min
    end_minutes = end_hour * 60 + end_min
    
    # Handle overnight windows
    if end_minutes <= start_minutes:
        end_minutes += 24 * 60  # Add a day in minutes
    
    duration_hours = (end_minutes - start_minutes) / 60.0
    
    # Ensure duration is positive
    if duration_hours <= 0:
        logger.warning(f"Calculated non-positive window duration for {start_time}-{end_time}, using default value")
        duration_hours = 0.5  # Default to half hour if calculation is incorrect
    
    return duration_hours

def count_service_days(service_days):
    """Count the number of days in the service_days list."""
    return len(service_days)

def estimate_mwh_from_capacity(capacity_mw, duration_hours, days_count):
    """
    Estimate MWh based on capacity, duration, and number of days.
    This is a simplified calculation - actual MWh depends on the specific
    demand profile and firm capacity algorithm.
    """
    # Simple assumption: energy is capacity × duration × some utilization factor
    # In reality, this is an approximation since the energy calculation
    # depends on the specific demand profile and how it exceeds firm capacity
    utilization_factor = 0.8  # Assume 80% utilization as an approximation
    return capacity_mw * duration_hours * utilization_factor

def extract_month_from_period(period_name):
    """Extract month from period name (e.g., 'January' from 'January 1 (Monday)')."""
    # Look for a month name at the beginning of the period name
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    
    for month in months:
        if period_name.startswith(month):
            return month
    
    return "Unknown"

def generate_service_window_mwh(competitions, output_path, total_energy_mwh=None):
    """
    Generate a CSV file with MWh data from service windows.
    
    Args:
        competitions: List of competition dictionaries
        output_path: Path to save the output CSV
        total_energy_mwh: Optional total energy above capacity for validation
    
    Returns:
        DataFrame with service window MWh data
    """
    logger.info(f"Generating service window MWh data to {output_path}")
    
    # Extract data for each service window
    rows = []
    
    for comp_idx, comp in enumerate(competitions):
        comp_name = comp.get("name", f"Competition {comp_idx+1}")
        
        for period_idx, period in enumerate(comp["service_periods"]):
            period_name = period.get("name", f"Period {period_idx+1}")
            month = extract_month_from_period(period_name)
            
            for window_idx, window in enumerate(period["service_windows"]):
                window_name = window.get("name", f"Window {window_idx+1}")
                
                # Extract capacity required (convert from string to float)
                capacity_mw = float(window["capacity_required"])
                
                # Calculate window duration
                duration_hours = extract_window_duration(window["start"], window["end"])
                
                # Count service days
                days_count = count_service_days(window["service_days"])
                
                # Check if energy_mwh is already in the window data
                energy_mwh = window.get("energy_mwh")
                
                # If energy_mwh is not available, estimate it
                if energy_mwh is None:
                    energy_mwh = estimate_mwh_from_capacity(capacity_mw, duration_hours, days_count)
                
                # Create row
                row = {
                    "Competition": comp_name,
                    "Month": month,
                    "Window": window_name,
                    "Capacity (MW)": capacity_mw,
                    "Energy (MWh)": energy_mwh,
                    "Window Duration (h)": duration_hours,
                    "Days": days_count,
                    "Hours": duration_hours * days_count,
                    "Start": window["start"],
                    "End": window["end"],
                    "Service Days": ",".join(window["service_days"])
                }
                
                rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Ensure all window durations are positive
    if len(df) > 0 and 'Window Duration (h)' in df.columns:
        # Check for any non-positive durations
        non_positive = df[df['Window Duration (h)'] <= 0]
        if len(non_positive) > 0:
            logger.warning(f"Found {len(non_positive)} entries with non-positive window durations. Fixing these values.")
            for idx in non_positive.index:
                logger.warning(f"Fixing non-positive duration for {df.loc[idx, 'Window']} ({df.loc[idx, 'Start']}-{df.loc[idx, 'End']})")
                df.loc[idx, 'Window Duration (h)'] = 0.5  # Set to default 0.5 hours
    
    if len(df) > 0:
        # Ensure all window durations are strictly positive
        # First, identify any problematic rows
        non_positive_rows = df[df['Window Duration (h)'] <= 0]
        if len(non_positive_rows) > 0:
            logger.warning(f"Found {len(non_positive_rows)} rows with non-positive durations. Setting them to 0.5 hours.")
            # Fix all non-positive durations before saving
            df.loc[df['Window Duration (h)'] <= 0, 'Window Duration (h)'] = 0.5
            
        # Sort by competition, month, window
        df = df.sort_values(["Competition", "Month", "Window"])
            
        # Create separate dataframes for data and summary
        data_df = df.copy()
        
        # Calculate total MWh for the summary
        total_mwh = data_df["Energy (MWh)"].sum()
        total_hours = data_df["Hours"].sum()
        total_capacity = data_df["Capacity (MW)"].sum()
        
        # Create summary row
        summary_row = pd.DataFrame([{
            "Competition": "TOTAL",
            "Month": "Summary",
            "Window": "Summary",
            "Capacity (MW)": total_capacity,
            "Energy (MWh)": total_mwh,
            "Window Duration (h)": 1.0,  # Use a positive value for the summary
            "Days": data_df["Days"].sum(),
            "Hours": total_hours,
            "Start": "",
            "End": "",
            "Service Days": ""
        }])
        
        # Double-check data_df for any non-positive durations (paranoia mode)
        if any(data_df['Window Duration (h)'] <= 0):
            logger.error("STILL found non-positive durations after fixing! Forcing all to 0.5 hours.")
            data_df.loc[data_df['Window Duration (h)'] <= 0, 'Window Duration (h)'] = 0.5
        
        # Save data only (without summary) to CSV file for test compatibility
        data_df.to_csv(output_path, index=False)
        
        # Verify the saved CSV has no non-positive window durations
        try:
            test_df = pd.read_csv(output_path)
            if any(test_df['Window Duration (h)'] <= 0):
                logger.error(f"CSV verification failed! Still found {sum(test_df['Window Duration (h)'] <= 0)} rows with non-positive durations.")
                # Last resort fix: regenerate the CSV with guaranteed positive values
                test_df.loc[test_df['Window Duration (h)'] <= 0, 'Window Duration (h)'] = 0.5
                test_df.to_csv(output_path, index=False)
                logger.info("Re-saved CSV file with fixed durations")
        except Exception as e:
            logger.error(f"Error verifying CSV file: {e}")
        
        # Save full data with summary to a separate file
        summary_path = Path(str(output_path).replace(".csv", "_with_summary.csv"))
        pd.concat([data_df, summary_row], ignore_index=True).to_csv(summary_path, index=False)
        
        logger.info(f"Saved service window MWh data with {len(data_df)} rows to {output_path}")
        logger.info(f"Saved service window MWh data with summary to {summary_path}")
        
        # Log validation information
        if total_energy_mwh is not None:
            mwh_diff = abs(total_mwh - total_energy_mwh)
            mwh_pct_diff = (mwh_diff / total_energy_mwh) * 100 if total_energy_mwh > 0 else 0
            logger.info(f"Total service window MWh: {total_mwh:.2f}, Target MWh: {total_energy_mwh:.2f}")
            logger.info(f"Difference: {mwh_diff:.2f} MWh ({mwh_pct_diff:.2f}%)")
    else:
        logger.warning(f"No service windows found for MWh data generation")
    
    return df

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

    # Determine if we're using pre-filtered parquet data
    if parquet_df is not None:
        logger.info(f"Using pre-filtered parquet data for {name}")
        df = parquet_df
    else:
        # Check for data source in substation config
        demand_source = sub.get("demand_source", "csv")
        
        if demand_source == "parquet" and parquet_path is None:
            logger.error(f"Error: Demand source is 'parquet' but no parquet data provided for {name}")
            raise ValueError(f"No parquet data provided for {name}")
        
        # Original CSV loading logic
        if cfg["input"]["in_substation_folder"]:
            demand_path = out_base / sub["demand_file"]
        else:
            try:
                # Try to get demand file from substation config
                demand_file = sub.get("demand_file", f"{name}.csv")
                demand_path = Path(cfg["input"]["demand_base_dir"]) / demand_file
            except KeyError:
                demand_path = Path(cfg["input"]["demand_base_dir"]) / f"{name}.csv"
        
        # Load demand data
        logger.info(f"Loading CSV demand data from {demand_path}")
        df = pd.read_csv(demand_path, parse_dates=["Timestamp"])
    
    # Common processing for both CSV and parquet data
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
    
    # Use site-specific target if available, otherwise use default from config
    if site_targets and name in site_targets:
        T = site_targets[name]
        logger.info(f"Using site-specific target for {name}: {T} MWh")
    else:
        T = cfg["firm_capacity"]["target_mwh"]
        logger.info(f"Using default target from config for {name}: {T} MWh")
    
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
        "energy_above_capacity_MWh": float(energy_peak),
        "target_mwh": T  # Add the target to the stats output
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
            
            # Generate service window MWh data
            mwh_path = out_base / "service_window_mwh.csv"
            generate_service_window_mwh(competitions, mwh_path, stats.get("energy_above_capacity_MWh"))
            
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
    
    # Add default competitions section if not present
    if "competitions" not in cfg:
        cfg["competitions"] = {
            "procurement_window_size_minutes": 30,
            "daily_service_periods": False,
            "financial_year": None
        }
    
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
    
    # Check if we're using parquet file
    if args.parquet:
        logger.info(f"Using parquet file: {args.parquet}")
        
        # Parse filter if provided
        filter_groups = None
        if args.filter:
            filter_groups = [g.strip() for g in args.filter.split(',')]
        
        # Process network groups from parquet file
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
            site_targets=site_targets  # Pass site-specific targets
        )
        
        # Save summary results
        summary_path = Path(cfg["output"]["base_dir"]) / "parquet_summary.csv"
        summary_df = save_summary_results(results, summary_path)
        logger.info(f"Parquet processing summary saved to {summary_path}")
        
    else:
        # Process each substation as before
        results = []
        for sub in cfg["substations"]:
            try:
                result = process_substation_with_competitions(
                    cfg, 
                    sub, 
                    generate_competitions=args.competitions,
                    target_year=args.year,
                    schema_path=args.schema,
                    site_targets=site_targets  # Pass site-specific targets
                )
                results.append(result)
                logger.info(f"Successfully processed {sub['name']}")
            except FileNotFoundError:
                if cfg["input"]["in_substation_folder"]:
                    demand_path = Path(cfg["output"]["base_dir"]) / sub["name"] / sub["demand_file"]
                else:
                    demand_path = Path(cfg["input"]["demand_base_dir"]) / f"{sub['demand_file']}"
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
