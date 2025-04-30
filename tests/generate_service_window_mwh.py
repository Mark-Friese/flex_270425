#!/usr/bin/env python3
"""
generate_service_window_mwh.py - Extracts MWh data from service windows in competitions

This script creates a CSV file with energy (MWh) values for each service window
in the competitions, useful for energy consistency testing.
"""

import json
import pandas as pd
from pathlib import Path
import argparse
import logging
import re
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_window_duration(start_time, end_time):
    """
    Calculate window duration in hours from start and end times (HH:MM format).
    Handles overnight windows.
    """
    start_hour, start_min = map(int, start_time.split(':'))
    end_hour, end_min = map(int, end_time.split(':'))
    
    start_minutes = start_hour * 60 + start_min
    end_minutes = end_hour * 60 + end_min
    
    # Handle overnight windows
    if end_minutes <= start_minutes:
        end_minutes += 24 * 60  # Add a day in minutes
    
    duration_hours = (end_minutes - start_minutes) / 60.0
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

def process_competitions(competitions_path, output_path):
    """
    Process competitions to extract service window MWh data.
    
    Args:
        competitions_path: Path to competitions.json file
        output_path: Path to save the output CSV
    """
    logger.info(f"Processing competitions from {competitions_path}")
    
    # Load competitions JSON
    with open(competitions_path) as f:
        competitions = json.load(f)
    
    logger.info(f"Found {len(competitions)} competitions")
    
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
                
                # Check if energy_mwh is already in the window data (it might be removed in the final output)
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
    
    # Add calculated columns
    df["Energy per Hour (MWh/h)"] = df["Energy (MWh)"] / df["Hours"]
    df["Energy / Capacity × Duration Ratio"] = df["Energy (MWh)"] / (df["Capacity (MW)"] * df["Hours"])
    
    # Sort by competition, month, window
    df = df.sort_values(["Competition", "Month", "Window"])
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved service window MWh data to {output_path}")
    
    return df

def main():
    parser = argparse.ArgumentParser(description="Extract MWh data from service windows")
    parser.add_argument("--competitions", type=str, help="Path to competitions.json file")
    parser.add_argument("--output", type=str, help="Path to save the output CSV")
    parser.add_argument("--substations", type=str, nargs="+", default=["Monktonhall"], 
                        help="List of substations to process")
    parser.add_argument("--output-dir", type=str, default="output", 
                        help="Base directory for outputs")
    
    args = parser.parse_args()
    
    # Process each substation
    for sub in args.substations:
        logger.info(f"Processing substation: {sub}")
        
        if args.competitions:
            competitions_path = args.competitions
        else:
            competitions_path = Path(args.output_dir) / sub / "competitions.json"
        
        if args.output:
            output_path = args.output
        else:
            output_path = Path(args.output_dir) / sub / "service_window_mwh.csv"
        
        if not Path(competitions_path).exists():
            logger.error(f"Competitions file not found: {competitions_path}")
            continue
        
        try:
            df = process_competitions(competitions_path, output_path)
            logger.info(f"Successfully processed {sub}: {len(df)} service windows")
        except Exception as e:
            logger.error(f"Error processing {sub}: {e}", exc_info=True)

if __name__ == "__main__":
    main()