#!/usr/bin/env python3
"""
test_firm_capacity.py - Tests for firm capacity calculations
"""

import unittest
import json
import pandas as pd
import numpy as np
from pathlib import Path

class FirmCapacityTest(unittest.TestCase):
    
    def setUp(self):
        # Paths to reference and output directories
        self.reference_dir = Path("tests/reference_data")
        self.output_dir = Path("output")
        
        # Substations to test - can be made configurable
        self.substations = ["Monktonhall"]  # Update with the substations you're testing
        
        # Tolerance for floating point comparisons
        self.float_tolerance = 1e-4
    
    def test_firm_capacity_values(self):
        """Test that firm capacity values are consistent with reference data."""
        for sub in self.substations:
            # Load reference and new metadata
            ref_meta_path = self.reference_dir / sub / "metadata.json"
            new_meta_path = self.output_dir / sub / "metadata.json"
            
            self.assertTrue(ref_meta_path.exists(), f"Reference metadata not found for {sub}")
            self.assertTrue(new_meta_path.exists(), f"New metadata not found for {sub}")
            
            with open(ref_meta_path) as f:
                ref_meta = json.load(f)
            
            with open(new_meta_path) as f:
                new_meta = json.load(f)
            
            # Check firm capacity values (both plain and peak)
            self.assertAlmostEqual(
                ref_meta["C_plain_MW"], 
                new_meta["C_plain_MW"],
                delta=self.float_tolerance,
                msg=f"Plain firm capacity changed for {sub}"
            )
            
            self.assertAlmostEqual(
                ref_meta["C_peak_MW"], 
                new_meta["C_peak_MW"],
                delta=self.float_tolerance,
                msg=f"Peak firm capacity changed for {sub}"
            )
    
    def test_demand_statistics(self):
        """Test that demand statistics are consistent with reference data."""
        for sub in self.substations:
            # Load reference and new metadata
            ref_meta_path = self.reference_dir / sub / "metadata.json"
            new_meta_path = self.output_dir / sub / "metadata.json"
            
            with open(ref_meta_path) as f:
                ref_meta = json.load(f)
            
            with open(new_meta_path) as f:
                new_meta = json.load(f)
            
            # Check mean demand
            self.assertAlmostEqual(
                ref_meta["mean_demand_MW"], 
                new_meta["mean_demand_MW"],
                delta=self.float_tolerance,
                msg=f"Mean demand changed for {sub}"
            )
            
            # Check max demand
            self.assertAlmostEqual(
                ref_meta["max_demand_MW"], 
                new_meta["max_demand_MW"],
                delta=self.float_tolerance,
                msg=f"Max demand changed for {sub}"
            )
            
            # Check total energy
            self.assertAlmostEqual(
                ref_meta["total_energy_MWh"], 
                new_meta["total_energy_MWh"],
                delta=self.float_tolerance,
                msg=f"Total energy changed for {sub}"
            )
    
    def test_firm_capacity_results_csv(self):
        """Test that firm_capacity_results.csv is consistent with reference data."""
        for sub in self.substations:
            # Load reference and new CSV files
            ref_csv_path = self.reference_dir / sub / "firm_capacity_results.csv"
            new_csv_path = self.output_dir / sub / "firm_capacity_results.csv"
            
            self.assertTrue(ref_csv_path.exists(), f"Reference CSV not found for {sub}")
            self.assertTrue(new_csv_path.exists(), f"New CSV not found for {sub}")
            
            ref_df = pd.read_csv(ref_csv_path)
            new_df = pd.read_csv(new_csv_path)
            
            # Check that dataframes have the same columns
            self.assertListEqual(
                list(ref_df.columns), 
                list(new_df.columns),
                f"CSV columns changed for {sub}"
            )
            
            # Check that values are similar (within tolerance)
            for col in ref_df.columns:
                if col == 'substation':  # Skip string columns
                    continue
                
                self.assertAlmostEqual(
                    ref_df[col].iloc[0], 
                    new_df[col].iloc[0],
                    delta=self.float_tolerance,
                    msg=f"Value in column {col} changed for {sub}"
                )

if __name__ == '__main__':
    unittest.main()