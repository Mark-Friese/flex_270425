#!/usr/bin/env python3
"""
copy_reference_data.py - Creates reference datasets for testing from existing outputs
"""

import os
import shutil
from pathlib import Path
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_reference_data(output_dir, reference_dir):
    """
    Copy output data to a reference directory for testing
    
    Args:
        output_dir: Path to output directory with generated results
        reference_dir: Path to reference directory for testing
    """
    output_path = Path(output_dir)
    reference_path = Path(reference_dir)
    
    # Create reference directory if it doesn't exist
    reference_path.mkdir(parents=True, exist_ok=True)
    
    # Get a list of all substation directories in the output dir
    substation_dirs = [d for d in output_path.iterdir() if d.is_dir()]
    
    for substation in substation_dirs:
        substation_name = substation.name
        logger.info(f"Processing substation: {substation_name}")
        
        # Create reference subdirectory for this substation
        ref_substation_dir = reference_path / substation_name
        ref_substation_dir.mkdir(parents=True, exist_ok=True)
        
        # Files to copy (key files for testing)
        files_to_copy = [
            "firm_capacity_results.csv",
            "metadata.json",
            "competitions.json",
            "E_curve_peak.png",
            "E_curve_plain.png"
        ]
        
        # Copy each file if it exists
        for filename in files_to_copy:
            src_file = substation / filename
            if src_file.exists():
                dst_file = ref_substation_dir / filename
                shutil.copy2(src_file, dst_file)
                logger.info(f"Copied {filename} to reference data")
            else:
                logger.warning(f"File {filename} not found in {substation}")
        
        # Also copy the demand.csv file if it exists
        demand_file = substation / "demand.csv"
        if demand_file.exists():
            dst_file = ref_substation_dir / "demand.csv"
            shutil.copy2(demand_file, dst_file)
            logger.info("Copied demand.csv to reference data")

def main():
    parser = argparse.ArgumentParser(description="Create reference datasets for testing")
    parser.add_argument("--output-dir", type=str, default="output", 
                        help="Path to output directory with generated results")
    parser.add_argument("--reference-dir", type=str, default="tests/reference_data", 
                        help="Path to reference directory for testing")
    
    args = parser.parse_args()
    
    # Use absolute paths if not provided
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        # Assuming this script is run from the project root
        output_dir = Path.cwd() / args.output_dir
    
    reference_dir = Path(args.reference_dir)
    if not reference_dir.is_absolute():
        reference_dir = Path.cwd() / args.reference_dir
    
    logger.info(f"Copying data from {output_dir} to {reference_dir}")
    create_reference_data(output_dir, reference_dir)
    logger.info("Reference data creation complete!")

if __name__ == "__main__":
    main()