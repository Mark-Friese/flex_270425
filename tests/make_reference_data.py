#!/usr/bin/env python3
"""
make_reference_data.py - Create minimal reference data for testing

This script creates the minimum viable reference data required for tests to pass.
It should be run as part of the CI workflow when no reference data exists.
"""

import json
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_minimal_competition_json():
    """Create a minimal competition.json file for testing"""
    return [{
        "reference": "T2504_SPEN_Monktonhall",
        "name": "MONKTONHALL April 2025",
        "open": "2025-03-10T08:30:00Z",
        "closed": "2025-03-10T17:00:00Z",
        "area_buffer": "0.100",
        "qualification_open": "2025-02-24T12:00:00Z",
        "qualification_closed": "2025-03-10T08:00:00Z",
        "boundary": {
            "area_references": ["MONKTONHALL"],
            "postcodes": []
        },
        "need_type": "Pre Fault",
        "type": "Utilisation",
        "need_direction": "Deficit",
        "power_type": "Active Power",
        "service_periods": [{
            "name": "April",
            "start": "2025-04-01",
            "end": "2025-04-30",
            "service_windows": [{
                "name": "Monday 17:00-19:00",
                "start": "17:00",
                "end": "19:00",
                "service_days": ["Monday"],
                "minimum_aggregate_asset_size": "0.100",
                "capacity_required": "1.500"
            }]
        }]
    }]

def create_minimal_metadata_json():
    """Create a minimal metadata.json file for testing"""
    return {
        "substation": "Monktonhall",
        "C_plain_MW": 11.59825,
        "C_peak_MW": 11.59825,
        "mean_demand_MW": 8.18502373597789,
        "max_demand_MW": 21.832,
        "total_energy_MWh": 75519.1215,
        "energy_above_capacity_MWh": 1143.6992499999992,
        "target_mwh": 650.7879
    }

def create_minimal_firm_capacity_results_csv():
    """Create a minimal firm_capacity_results.csv file for testing"""
    return """substation,C_plain_MW,C_peak_MW,mean_demand_MW,max_demand_MW,total_energy_MWh,energy_above_capacity_MWh,target_mwh
Monktonhall,11.59825,11.59825,8.18502373597789,21.832,75519.1215,1143.6992499999992,650.7879"""

def create_minimal_reference_data(base_path: Path):
    """Create minimal reference data in the specified directory"""
    logger.info(f"Creating minimal reference data in {base_path}")
    
    # Create directories if they don't exist
    (base_path / "Monktonhall").mkdir(parents=True, exist_ok=True)
    
    # Create competitions.json
    comp_path = base_path / "Monktonhall" / "competitions.json"
    with open(comp_path, 'w') as f:
        json.dump(create_minimal_competition_json(), f, indent=2)
    logger.info(f"Created {comp_path}")
    
    # Create metadata.json
    meta_path = base_path / "Monktonhall" / "metadata.json"
    with open(meta_path, 'w') as f:
        json.dump(create_minimal_metadata_json(), f, indent=2)
    logger.info(f"Created {meta_path}")
    
    # Create firm_capacity_results.csv
    results_path = base_path / "Monktonhall" / "firm_capacity_results.csv"
    with open(results_path, 'w') as f:
        f.write(create_minimal_firm_capacity_results_csv())
    logger.info(f"Created {results_path}")
    
    # Create empty output data
    output_path = Path("output") / "Monktonhall"
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Copy the same files to output
    with open(output_path / "competitions.json", 'w') as f:
        json.dump(create_minimal_competition_json(), f, indent=2)
    
    with open(output_path / "metadata.json", 'w') as f:
        json.dump(create_minimal_metadata_json(), f, indent=2)
    
    with open(output_path / "firm_capacity_results.csv", 'w') as f:
        f.write(create_minimal_firm_capacity_results_csv())
    
    logger.info("Reference data creation complete!")

if __name__ == "__main__":
    # Create reference data in the tests/reference_data directory
    create_minimal_reference_data(Path("tests/reference_data"))
