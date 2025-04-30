#!/usr/bin/env python3
"""
test_service_windows.py - Tests for service window generation
"""

import unittest
import json
import pandas as pd
import numpy as np
from pathlib import Path
import os

class ServiceWindowsTest(unittest.TestCase):
    
    def setUp(self):
        # Paths to reference and output directories
        self.reference_dir = Path("tests/reference_data")
        self.output_dir = Path("output")
        
        # Substations to test - can be made configurable
        self.substations = ["Monktonhall"]  # Update with the substations you're testing
        
        # Create a helper function to extract all service windows from competitions
        def extract_service_windows(competitions):
            windows = []
            for comp_idx, comp in enumerate(competitions):
                for period_idx, period in enumerate(comp["service_periods"]):
                    for window_idx, window in enumerate(period["service_windows"]):
                        window_data = {
                            "competition_idx": comp_idx,
                            "competition_name": comp["name"],
                            "period_idx": period_idx,
                            "period_name": period["name"],
                            "window_idx": window_idx,
                            "window_name": window["name"],
                            "start": window["start"],
                            "end": window["end"],
                            "capacity_required": float(window["capacity_required"]),
                            "service_days": ','.join(window["service_days"])
                        }
                        windows.append(window_data)
            return pd.DataFrame(windows)
        
        self.extract_service_windows = extract_service_windows
    
    def test_service_window_energy_consistency(self):
        """Test that service window energy calculations are consistent with reference data."""
        for sub in self.substations:
            # Create directory for test artifacts if it doesn't exist
            test_output_dir = Path("tests/output")
            test_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Load reference and new competition files
            ref_comp_path = self.reference_dir / sub / "competitions.json"
            new_comp_path = self.output_dir / sub / "competitions.json"
            
            with open(ref_comp_path) as f:
                ref_comps = json.load(f)
            
            with open(new_comp_path) as f:
                new_comps = json.load(f)
            
            # Extract service windows from both datasets
            ref_windows = self.extract_service_windows(ref_comps)
            new_windows = self.extract_service_windows(new_comps)
            
            # Save to CSV for debugging
            ref_windows.to_csv(test_output_dir / f"{sub}_ref_windows.csv", index=False)
            new_windows.to_csv(test_output_dir / f"{sub}_new_windows.csv", index=False)
            
            # Check that window counts match
            self.assertEqual(
                len(ref_windows), 
                len(new_windows),
                f"Number of service windows changed for {sub}"
            )
            
            # Check window capacities by matching on window name
            ref_windows_dict = {row['window_name']: row for _, row in ref_windows.iterrows()}
            new_windows_dict = {row['window_name']: row for _, row in new_windows.iterrows()}
            
            for window_name, ref_row in ref_windows_dict.items():
                self.assertIn(window_name, new_windows_dict, f"Window {window_name} missing in new data for {sub}")
                
                new_row = new_windows_dict[window_name]
                
                # Check capacity required
                self.assertAlmostEqual(
                    ref_row["capacity_required"], 
                    new_row["capacity_required"],
                    delta=0.001,  # Allow small differences due to floating point
                    msg=f"Capacity requirement changed for window {window_name} in {sub}"
                )
                
                # Check start and end times
                self.assertEqual(
                    ref_row["start"], 
                    new_row["start"],
                    f"Start time changed for window {window_name} in {sub}"
                )
                
                self.assertEqual(
                    ref_row["end"], 
                    new_row["end"],
                    f"End time changed for window {window_name} in {sub}"
                )
    
    def test_service_window_mwh_file(self):
        """
        Test the service_window_mwh.csv file if it exists.
        This is a placeholder for when you add this additional output.
        """
        for sub in self.substations:
            mwh_file = self.output_dir / sub / "service_window_mwh.csv"
            
            # Skip if the file doesn't exist yet
            if not mwh_file.exists():
                self.skipTest(f"service_window_mwh.csv not found for {sub}")
                continue
            
            # Load the file
            df = pd.read_csv(mwh_file)
            
            # Check required columns
            required_columns = [
                'Competition', 'Month', 'Window', 'Capacity (MW)', 
                'Energy (MWh)', 'Hours', 'Days', 'Window Duration (h)'
            ]
            
            for col in required_columns:
                self.assertIn(col, df.columns, f"Missing column {col} in MWh file for {sub}")
            
            # Check no negative values for key metrics
            self.assertTrue(all(df['Capacity (MW)'] >= 0), "Negative capacity values found")
            self.assertTrue(all(df['Energy (MWh)'] >= 0), "Negative energy values found")
            self.assertTrue(all(df['Window Duration (h)'] > 0), "Non-positive window duration found")
            
            # Check that MWh values make sense (should be capacity × duration × utilization factor)
            # This is an approximate check since the exact calculation depends on your implementation
            df['Calculated MWh'] = df['Capacity (MW)'] * df['Window Duration (h)']
            df['MWh Ratio'] = df['Energy (MWh)'] / df['Calculated MWh']
            
            # MWh should be less than or equal to capacity × duration (utilization < 100%)
            self.assertTrue(all(df['MWh Ratio'] <= 1.01), "Energy exceeds capacity × duration by >1%")
            
            # Save the verification data for manual inspection
            test_output_dir = Path("tests/output")
            test_output_dir.mkdir(parents=True, exist_ok=True)
            df.to_csv(test_output_dir / f"{sub}_mwh_verification.csv", index=False)

if __name__ == '__main__':
    unittest.main()