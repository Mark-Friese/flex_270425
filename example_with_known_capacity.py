#!/usr/bin/env python3
"""
Example: Generate service windows with a known firm capacity

This script demonstrates how to generate service windows and competitions
when you already have a firm capacity value, without needing to calculate it.
"""

import pandas as pd
from pathlib import Path
import logging

# Import the competition builder directly
from competition_builder import create_competitions_from_df, save_competitions_to_json
from firm_capacity_with_competitions import generate_service_window_mwh

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_service_windows_with_known_capacity(
    demand_file: str,
    firm_capacity: float,
    output_dir: str = "output",
    substation_name: str = "Example_Substation"
):
    """
    Generate service windows using a pre-calculated firm capacity.
    
    Args:
        demand_file: Path to CSV file with demand data (must have 'Timestamp' and 'Demand (MW)' columns)
        firm_capacity: Firm capacity in MW
        output_dir: Directory to save results
        substation_name: Name of the substation
    """
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Load demand data
    logger.info(f"Loading demand data from {demand_file}")
    df = pd.read_csv(demand_file, parse_dates=["Timestamp"])
    df = df.sort_values("Timestamp")
    
    # Add substation name if not present
    if "Substation" not in df.columns:
        df["Substation"] = substation_name
    
    # Determine time step from data
    if len(df) > 1:
        time_diff = (df["Timestamp"].iloc[1] - df["Timestamp"].iloc[0]).total_seconds() / 3600
        delta_t = time_diff
    else:
        delta_t = 0.5  # Default to half-hourly
    
    logger.info(f"Using firm capacity: {firm_capacity:.2f} MW")
    logger.info(f"Detected time step: {delta_t} hours")
    
    # Generate competitions directly with the known firm capacity
    competitions = create_competitions_from_df(
        df,
        firm_capacity,  # Use the provided firm capacity
        procurement_window_size_minutes=30,
        daily_service_periods=False,  # Group by month
        delta_t=delta_t
    )
    
    if competitions:
        # Save competitions to JSON
        competitions_path = output_path / "competitions.json"
        save_competitions_to_json(competitions, str(competitions_path))
        logger.info(f"Saved {len(competitions)} competitions to {competitions_path}")
        
        # Generate service window MWh data
        mwh_path = output_path / "service_window_mwh.csv"
        mwh_df = generate_service_window_mwh(competitions, mwh_path)
        
        # Print summary
        total_windows = len(mwh_df) if not mwh_df.empty else 0
        total_mwh = mwh_df["Energy (MWh)"].sum() if not mwh_df.empty else 0
        
        logger.info(f"Generated {total_windows} service windows")
        logger.info(f"Total energy above capacity: {total_mwh:.2f} MWh")
        
        # Print a few example windows
        if not mwh_df.empty:
            logger.info("\nExample service windows:")
            for idx, row in mwh_df.head(3).iterrows():
                logger.info(f"  {row['Window']}: {row['Capacity (MW)']:.2f} MW, {row['Energy (MWh)']:.2f} MWh")
        
        return competitions, mwh_df
    else:
        logger.warning("No service windows generated - demand may not exceed firm capacity")
        return [], pd.DataFrame()

def main():
    """Example usage"""
    # Example parameters - adjust these for your use case
    demand_file = "data/samples/example_demand.csv"  # Path to your demand data
    firm_capacity = 25.0  # Your known firm capacity in MW
    output_dir = "example_output"
    substation_name = "Example_Substation"
    
    try:
        competitions, mwh_df = generate_service_windows_with_known_capacity(
            demand_file=demand_file,
            firm_capacity=firm_capacity,
            output_dir=output_dir,
            substation_name=substation_name
        )
        
        print(f"\n✅ Successfully generated service windows!")
        print(f"📁 Results saved to: {output_dir}/")
        print(f"📊 {len(competitions)} competitions created")
        if not mwh_df.empty:
            print(f"⚡ {len(mwh_df)} service windows with {mwh_df['Energy (MWh)'].sum():.2f} MWh total")
        
    except FileNotFoundError:
        print(f"❌ Error: Could not find demand file: {demand_file}")
        print("Please ensure your demand file exists and has 'Timestamp' and 'Demand (MW)' columns")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 